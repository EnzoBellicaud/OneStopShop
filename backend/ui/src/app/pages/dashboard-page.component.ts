import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, forkJoin, takeUntil } from 'rxjs';
import {
  DashboardResponse,
  DomainLookup,
  MatchingHit,
  MatchingHitsQueryParams,
  Offer,
  TargetProfileLookup,
  UserFavorite,
  UserNeed,
  UserNeedCreateRequest,
  UserNeedUpdateRequest,
} from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard-page.component.html',
  styleUrl: './dashboard-page.component.css',
})
export class DashboardPageComponent implements OnInit, OnDestroy {
  readonly needStatuses: Array<UserNeed['status']> = ['active', 'fulfilled', 'archived'];
  readonly matchingStatuses: Array<MatchingHit['status']> = ['new', 'viewed', 'interested', 'declined'];
  readonly updateableMatchStatuses: Array<'viewed' | 'interested' | 'declined'> = ['viewed', 'interested', 'declined'];

  dashboard: DashboardResponse | null = null;
  needs: UserNeed[] = [];
  favorites: UserFavorite[] = [];
  matchingHits: MatchingHit[] = [];
  domains: DomainLookup[] = [];
  targetProfiles: TargetProfileLookup[] = [];
  offers: Offer[] = [];

  userDraft = { userId: localStorage.getItem('oss.dashboard.userId') ?? '' };
  selectedNeedStatus: UserNeed['status'] = 'active';
  selectedMatchStatus: MatchingHitsQueryParams['status'] | '' = '';
  selectedMatchSort: MatchingHitsQueryParams['sort'] = '-match_score';
  offerSearch = '';

  loading = false;
  savingUser = false;
  savingNeed = false;
  savingFavorite = false;
  updatingMatch = '';
  errorMessage = '';
  userReady = false;

  editingNeedId: string | null = null;
  needForm: UserNeedUpdateRequest = this.emptyNeedForm();
  favoriteForm = {
    offer_id: '',
    note: '',
  };

  private readonly destroy$ = new Subject<void>();
  private userId = localStorage.getItem('oss.dashboard.userId') ?? '';

  constructor(private readonly api: OssApiService) {}

  ngOnInit(): void {
    this.bootstrapUserAndLoad();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  get filteredOfferOptions(): Offer[] {
    const search = this.offerSearch.trim().toLowerCase();
    return this.offers.filter((offer) => {
      const matchesSearch = search
        ? offer.title.toLowerCase().includes(search) || offer.organization.name.toLowerCase().includes(search)
        : true;
      const alreadySaved = this.favorites.some((favorite) => favorite.offer.id === offer.id);
      return matchesSearch && !alreadySaved;
    });
  }

  get selectedUserLabel(): string {
    if (!this.dashboard) {
      return this.userDraft.userId || '—';
    }

    return `${this.dashboard.user.username} (${this.dashboard.user.email})`;
  }

  trackNeed(_index: number, need: UserNeed): string {
    return need.id;
  }

  trackFavorite(_index: number, favorite: UserFavorite): string {
    return favorite.id;
  }

  trackMatch(_index: number, hit: MatchingHit): string {
    return hit.id;
  }

  domainLabel(domainId: string): string {
    return this.domains.find((domain) => domain.id === domainId)?.name ?? domainId.slice(0, 8);
  }

  saveIdentity(): void {
    this.bootstrapUserAndLoad();
  }

  applyNeedFilter(status: UserNeed['status']): void {
    this.selectedNeedStatus = status;
    this.loadNeeds();
  }

  applyMatchFilter(status: MatchingHitsQueryParams['status'] | ''): void {
    this.selectedMatchStatus = status;
    this.loadMatchingHits();
  }

  applyMatchSort(sort: MatchingHitsQueryParams['sort']): void {
    this.selectedMatchSort = sort;
    this.loadMatchingHits();
  }

  startCreateNeed(): void {
    this.editingNeedId = null;
    this.needForm = this.emptyNeedForm();
  }

  startEditNeed(need: UserNeed): void {
    this.editingNeedId = need.id;
    this.needForm = {
      title: need.title,
      description: need.description,
      status: need.status,
      target_profile_id: need.target_profile_id,
      domain_ids: [...need.domain_ids],
      countries: [...need.countries],
    };
  }

  cancelNeedEdit(): void {
    this.startCreateNeed();
  }

  submitNeed(): void {
    if (!this.userReady || !this.userId) {
      return;
    }

    this.savingNeed = true;
    this.errorMessage = '';

    const payload = {
      ...this.needForm,
      countries: this.needForm.countries.filter(Boolean),
      domain_ids: this.needForm.domain_ids.filter(Boolean),
    };

    const request = this.editingNeedId
      ? this.api.updateNeed(this.userId, this.editingNeedId, payload)
      : this.api.createNeed(this.userId, payload as UserNeedCreateRequest);

    request.pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.savingNeed = false;
        this.startCreateNeed();
        this.reloadDashboardData();
      },
      error: () => {
        this.savingNeed = false;
        this.errorMessage = 'Could not save the need. Verify the selected target profile and domains.';
      },
    });
  }

  deleteNeed(needId: string): void {
    if (!this.userReady || !this.userId) {
      return;
    }

    this.api.deleteNeed(this.userId, needId).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        if (this.editingNeedId === needId) {
          this.startCreateNeed();
        }
        this.reloadDashboardData();
      },
      error: () => {
        this.errorMessage = 'Could not delete the need.';
      },
    });
  }

  addFavorite(): void {
    if (!this.userReady || !this.userId || !this.favoriteForm.offer_id) {
      return;
    }

    this.savingFavorite = true;
    this.errorMessage = '';

    this.api.addFavorite(this.userId, this.favoriteForm).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.savingFavorite = false;
        this.favoriteForm = { offer_id: '', note: '' };
        this.offerSearch = '';
        this.reloadDashboardData();
      },
      error: () => {
        this.savingFavorite = false;
        this.errorMessage = 'Could not save the favorite. The offer may already be saved.';
      },
    });
  }

  removeFavorite(offerId: string): void {
    if (!this.userReady || !this.userId) {
      return;
    }

    this.api.removeFavorite(this.userId, offerId).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => this.reloadDashboardData(),
      error: () => {
        this.errorMessage = 'Could not remove the favorite.';
      },
    });
  }

  updateMatchStatus(hitId: string, status: 'viewed' | 'interested' | 'declined'): void {
    if (!this.userReady || !this.userId) {
      return;
    }

    this.updatingMatch = hitId;
    this.api.updateMatchingHit(this.userId, hitId, status).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.updatingMatch = '';
        this.reloadDashboardData();
      },
      error: () => {
        this.updatingMatch = '';
        this.errorMessage = 'Could not update the match status.';
      },
    });
  }

  toggleNeedDomain(domainId: string, checked: boolean): void {
    const ids = new Set(this.needForm.domain_ids);
    if (checked) {
      ids.add(domainId);
    } else {
      ids.delete(domainId);
    }
    this.needForm.domain_ids = Array.from(ids);
  }

  updateCountryList(rawValue: string): void {
    this.needForm.countries = rawValue
      .split(',')
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean);
  }

  countryValue(): string {
    return this.needForm.countries.join(', ');
  }

  private bootstrapUserAndLoad(): void {
    const id = this.userDraft.userId.trim();
    if (!id) {
      this.errorMessage = 'Enter a user ID to load the dashboard.';
      return;
    }

    this.savingUser = true;
    this.errorMessage = '';
    this.userId = id;

    this.api.getUser(id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.savingUser = false;
        this.userReady = true;
        localStorage.setItem('oss.dashboard.userId', id);
        this.loadReferenceData();
        this.reloadDashboardData();
      },
      error: () => {
        this.savingUser = false;
        this.userReady = false;
        this.errorMessage = 'User not found. Enter a valid user UUID.';
      },
    });
  }

  private reloadDashboardData(): void {
    if (!this.userReady || !this.userId) {
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    forkJoin({
      dashboard: this.api.getDashboard(this.userId),
      needs: this.api.getNeeds(this.userId, {
        status: this.selectedNeedStatus,
        page: 1,
        page_size: 12,
      }),
      favorites: this.api.getFavorites(this.userId, {
        page: 1,
        page_size: 12,
      }),
      matchingHits: this.api.getMatchingHits(this.userId, {
        status: this.selectedMatchStatus || undefined,
        sort: this.selectedMatchSort,
        page: 1,
        page_size: 12,
      }),
      offers: this.api.getOffers({
        status: 'published',
        page: 1,
        page_size: 50,
      }),
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ({ dashboard, needs, favorites, matchingHits, offers }) => {
          this.dashboard = dashboard;
          this.needs = needs.results;
          this.favorites = favorites.results;
          this.matchingHits = matchingHits.results;
          this.offers = offers.results;
          this.loading = false;
        },
        error: () => {
          this.loading = false;
          this.errorMessage = 'Could not load dashboard data. Check the API and seeded data.';
        },
      });
  }

  private loadReferenceData(): void {
    forkJoin({
      domains: this.api.getDomains(),
      targetProfiles: this.api.getTargetProfiles(),
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ({ domains, targetProfiles }) => {
          this.domains = domains.results;
          this.targetProfiles = targetProfiles.results;
          if (!this.needForm.target_profile_id && this.targetProfiles.length > 0) {
            this.needForm.target_profile_id = this.targetProfiles[0].id;
          }
        },
      });
  }

  private loadNeeds(): void {
    if (!this.userId) {
      return;
    }

    this.api.getNeeds(this.userId, {
      status: this.selectedNeedStatus,
      page: 1,
      page_size: 12,
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (payload) => {
          this.needs = payload.results;
          this.refreshDashboardOnly();
        },
      });
  }

  private loadMatchingHits(): void {
    if (!this.userId) {
      return;
    }

    this.api.getMatchingHits(this.userId, {
      status: this.selectedMatchStatus || undefined,
      sort: this.selectedMatchSort,
      page: 1,
      page_size: 12,
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (payload) => {
          this.matchingHits = payload.results;
          this.refreshDashboardOnly();
        },
      });
  }

  private refreshDashboardOnly(): void {
    if (!this.userId) {
      return;
    }

    this.api.getDashboard(this.userId).pipe(takeUntil(this.destroy$)).subscribe({
      next: (dashboard) => {
        this.dashboard = dashboard;
      },
    });
  }

  private emptyNeedForm(): UserNeedUpdateRequest {
    return {
      title: '',
      description: '',
      status: 'active',
      target_profile_id: this.targetProfiles[0]?.id ?? '',
      domain_ids: [],
      countries: [],
    };
  }

}
