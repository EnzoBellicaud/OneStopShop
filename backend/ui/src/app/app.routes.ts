import { Routes } from '@angular/router';
import { DashboardPageComponent } from './pages/dashboard-page.component';
import { ImportPageComponent } from './pages/import-page.component';
import { OffersPageComponent } from './pages/offers-page.component';
import { ScrapperAdminPageComponent } from './pages/scrapper-admin-page.component';

export const routes: Routes = [
	{
		path: '',
		pathMatch: 'full',
		redirectTo: 'dashboard',
	},
	{
		path: 'dashboard',
		component: DashboardPageComponent,
	},
	{
		path: 'offers',
		component: OffersPageComponent,
	},
	{
		path: 'admin/scrapper',
		component: ScrapperAdminPageComponent,
	},
	{
		path: 'admin/scraper',
		pathMatch: 'full',
		redirectTo: 'admin/scrapper',
	},
	{
		path: 'admin/import',
		component: ImportPageComponent,
	},
	{
		path: '**',
		redirectTo: 'offers',
	},
];
