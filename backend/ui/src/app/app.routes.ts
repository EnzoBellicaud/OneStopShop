import { Routes } from '@angular/router';
import { DashboardPageComponent } from './pages/dashboard-page.component';
import { ImportPageComponent } from './pages/import-page.component';
import { LoginPageComponent } from './pages/login-page.component';
import { MockSiteAdminPageComponent } from './pages/mock-site-admin-page.component';
import { OrganizationsAdminPageComponent } from './pages/organizations-admin-page.component';
import { SourcesAdminPageComponent } from './pages/sources-admin-page.component';
import { OffersAdminPageComponent } from './pages/offers-admin-page.component';
import { OffersPageComponent } from './pages/offers-page.component';
import { ScrapperAdminPageComponent } from './pages/scrapper-admin-page.component';
import { UsersPageComponent } from './pages/users-page.component';
import { DomainsPageComponent } from './pages/domains-page.component';
import { authGuard } from './shared/auth.guard';
import { adminGuard } from './shared/admin.guard';
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
		path: 'admin/users',
		component: UsersPageComponent,
		canActivate: [adminGuard],
	},
	{
		path: 'admin/domains',
		component: DomainsPageComponent,
		canActivate: [adminGuard],
	},
	{
		path: 'admin/offers',
		component: OffersAdminPageComponent,
		canActivate: [adminGuard],
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
		path: 'admin/mock-site',
		component: MockSiteAdminPageComponent,
		canActivate: [adminGuard],
	},
	{
		path: 'admin/organizations',
		component: OrganizationsAdminPageComponent,
		canActivate: [adminGuard],
	},
	{
		path: 'admin/sources',
		component: SourcesAdminPageComponent,
		canActivate: [adminGuard],
	},
	{
		path: '**',
		redirectTo: 'dashboard',
	},
];
