import { Routes } from '@angular/router';
import { DashboardPageComponent } from './pages/dashboard-page.component';
import { ImportPageComponent } from './pages/import-page.component';
import { LoginPageComponent } from './pages/login-page.component';
import { OffersPageComponent } from './pages/offers-page.component';
import { ScrapperAdminPageComponent } from './pages/scrapper-admin-page.component';
import { authGuard } from './shared/auth.guard';
import { guestGuard } from './shared/guest.guard';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'dashboard',
  },
  {
    path: 'login',
    component: LoginPageComponent,
    canActivate: [guestGuard],
  },
  {
    path: 'dashboard',
    component: DashboardPageComponent,
    canActivate: [authGuard],
  },
  {
    path: 'offers',
    component: OffersPageComponent,
    canActivate: [authGuard],
  },
  {
    path: 'admin/scrapper',
    component: ScrapperAdminPageComponent,
    canActivate: [authGuard],
  },
  {
    path: 'admin/scraper',
    pathMatch: 'full',
    redirectTo: 'admin/scrapper',
  },
  {
    path: 'admin/import',
    component: ImportPageComponent,
    canActivate: [authGuard],
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
