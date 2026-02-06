import { Routes } from '@angular/router';
import { AppComponent } from './app.component';

export const routes: Routes = [
  { path: '', redirectTo: '/research', pathMatch: 'full' },
  { path: 'research', component: AppComponent }
];
