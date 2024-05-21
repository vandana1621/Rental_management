from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('index/', views.index, name='index'),
    path('footer/', views.footer, name='footer'),
    path('head/', views.head, name='head'),
    path('header/', views.header, name='header'),
    path('navheader_view/', views.navheader_view, name='navheader_view'),
    path('sidebar/', views.index, name='sidebar'),
    path('app_calender/', views.app_calender, name='app_calender'),
    path('contact/', views.contact, name='contact'),
    path('performance/', views.performance, name='performance'),
    path('task/', views.task, name='task'),
    path('add_master_category/', views.add_category, name='add_category'),
    path('category_list/', views.category_list, name='category_list'),
    path('update_category/<int:category_id>/', views.update_category, name='update_category'),
    path('delete_category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('sub_category/', views.sub_category, name='sub_category'),
    path('category_dropdown/', views.category_dropdown, name='category_dropdown'),
    path('add_sub_category/', views.add_sub_category, name='add_sub_category'),
    path('subcategory_list/', views.subcategory_list, name='subcategory_list'),
    path('update_subcategory/<int:id>/', views.update_subcategory, name='update_subcategory'),
    path('delete_subcategory/<int:id>/', views.delete_subcategory, name='delete_subcategory'),
    path('add_user/', views.add_user, name='add_user'),
    path('user_list/', views.user_list, name='user_list'),
    path('update_user/<int:user_id>/', views.update_user, name='update_user'),
    path('delete_user/<int:id>/', views.delete_user, name='delete_user'),
    path('employee/', views.employee, name='employee'),
    path('add_employee/', views.add_employee, name='add_employee'),
    path('employee_dropdown/', views.employee_dropdown, name='employee_dropdown'),
    path('employee_list/', views.employee_list, name='employee_list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
