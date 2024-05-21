from datetime import datetime
from django.contrib.auth import login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.models import User
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import os

logger = logging.getLogger(__name__)


# Create your views here.
@login_required
def index(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return render(request, 'product_tracking/index.html', {'username': username})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not (username and password):
            messages.error(request, 'Username and password are required.')
            return render(request, 'product_tracking/page-login.html')

        user = authenticate_user(username, password)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'product_tracking/page-login.html',
                          {'error_message': 'Invalid username or password'})
    else:
        return render(request, 'product_tracking/page-login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def authenticate_user(username, password):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT validate_user(%s, %s, TRUE)", [username, password])
            if cursor.fetchone()[0]:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    logger.warning(
                        f"User '{username}' authenticated via PostgreSQL function but does not exist in Django.")
                    return None
                return user
            else:
                logger.info(f"Failed authentication attempt for user '{username}'.")
                return None
    except Exception as e:
        logger.exception("Error occurred during user authentication.")
        return None


def footer(request):
    return render(request, 'product_tracking/footer.html')


def head(request):
    return render(request, 'product_tracking/head.html')


def header(request):
    return render(request, 'product_tracking/header.html')


def navheader_view(request):
    return render(request, 'product_tracking/navheader.html')


def sidebar(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return render(request, 'product_tracking/sidebar.html', {'username': username})


def app_calender(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return render(request, 'product_tracking/app-calender.html', {'username': username})


def contact(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return render(request, 'product_tracking/contacts.html', {'username': username})


def employee(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return render(request, 'product_tracking/employee.html', {'username': username})


def performance(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return render(request, 'product_tracking/performance.html', {'username': username})


def task(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return render(request, 'product_tracking/task.html', {'username': username})


@login_required
def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        description = request.POST.get('description')
        status = request.POST.get('status')
        created_by = request.user.id
        created_date = datetime.now()

        try:
            with connection.cursor() as cursor:
                # Check if the category already exists
                cursor.execute("SELECT COUNT(*) FROM master_category WHERE category_name = %s", [category_name])
                category_count = cursor.fetchone()[0]

                if category_count > 0:
                    return JsonResponse({'success': False, 'message': 'Category Already Exists!'})

                # If the category doesn't exist, insert it
                cursor.execute(
                    "SELECT add_category(%s, %s, %s, %s, %s);",
                    [category_name, description, status, created_by, created_date]
                )
                category_id = cursor.fetchone()[0]
            return JsonResponse({'success': True})
        except Exception as e:
            print("An unexpected error occurred:", e)
            return JsonResponse({'success': False, 'message': 'An unexpected error occurred'})
    else:
        username = None
        if request.user.is_authenticated:
            username = request.user.username
        return render(request, 'product_tracking/performance1.html', {'username': username})


@login_required
def category_list(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM get_category_details()")
        rows = cursor.fetchall()

    category_listing = []
    for row in rows:
        created_date = row[5].strftime('%d-%m-%Y')
        category_listing.append({
            'category_id': row[0],
            'category_name': row[1],
            'category_description': row[2],
            'status': row[3],
            'created_by': row[4],
            'created_date': created_date
        })
        print('Category show successfully', category_listing)
    return JsonResponse(category_listing, safe=False)


@login_required
def update_category(request, category_id):
    if request.method == 'POST':
        print('Received POST request to update category details')

        # Extract the form data
        category_name = request.POST.get('categoryName')
        category_description = request.POST.get('categoryDescription')
        status = request.POST.get('statusText')

        print('Received data:', {
            'category_id': category_id,
            'category_name': category_name,
            'category_description': category_description,
            'status': status,
        })

        try:
            with connection.cursor() as cursor:
                cursor.callproc('update_category', [category_id, category_name, category_description, status])
                updated_category_id = cursor.fetchone()[0]
                print(updated_category_id)
            return JsonResponse(
                {'message': 'Category details updated successfully', 'updated_category_id': updated_category_id})
        except Exception as e:
            return JsonResponse({'error': 'Failed to update category details', 'exception': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'})


@login_required
def delete_category(request, category_id):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.callproc('delete_category', [category_id])
            return JsonResponse({'message': 'Category deleted successfully', 'category_id:': category_id})
        except Exception as e:
            return JsonResponse({'error': 'Failed to delete category', 'exception': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def sub_category(request):
    return render(request, 'product_tracking/sub-performance1.html')


@login_required
def category_dropdown(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT category_id, category_name FROM get_category_details()')
            categories = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
            print('Categories fetched successfully:', categories)
            return JsonResponse({'categories': categories}, safe=False)
    except Exception as e:
        # Handle exceptions, maybe log the error for debugging
        print("Error fetching categories:", e)
        return JsonResponse({'categories': []})


@login_required
def add_sub_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_name')
        subcategory_name = request.POST.get('subcategory_name')
        status = request.POST.get('status')
        created_by = request.user.id
        created_date = datetime.now()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT add_sub_category(%s, %s, %s, %s, %s);",
                    [category_id, subcategory_name, status, created_by, created_date]
                )
                return JsonResponse({'success': True})
        except Exception as e:
            if 'Subcategory already exists' in str(e):
                return JsonResponse({'success': False, 'message': 'Sub Category Already Exists!'})
            else:
                print("An unexpected error occurred:", e)
                return JsonResponse({'success': False, 'message': 'An unexpected error occurred'})
    else:
        username = None
        if request.user.is_authenticated:
            username = request.user.username
        categories = subcategory_list(request)  # Function to get all categories
        return render(request, 'product_tracking/sub-performance1.html', {'username': username, 'categories': categories})


@login_required
def subcategory_list(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM get_sub()")
        rows = cursor.fetchall()

    subcategory_listing = []
    for row in rows:
        created_date = row[5].strftime('%d-%m-%Y')
        subcategory_listing.append({
            'id': row[0],
            'category_name': row[1],
            'name': row[2],
            'status': row[3],
            'created_by': row[4],
            'created_date': created_date
        })
        print('Sub Category show successfully', subcategory_listing)
    return JsonResponse(subcategory_listing, safe=False)


@login_required
def update_subcategory(request, id):
    if request.method == 'POST':
        print('Received POST request to update sub category details')

        # Extract the form data
        name = request.POST.get('categoryName')
        status = request.POST.get('statusText')

        print('Received data:', {
            'id': id,
            'name': name,
            'status': status,
        })

        try:
            with connection.cursor() as cursor:
                cursor.callproc('update_subcategory', [id, name, status])
                updated_category_id = cursor.fetchone()[0]
                print(updated_category_id)
            return JsonResponse(
                {'message': 'Sub Category details updated successfully', 'updated_category_id': updated_category_id})
        except Exception as e:
            return JsonResponse({'error': 'Failed to update sub category details', 'exception': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'})


@login_required
def delete_subcategory(request, id):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.callproc('delete_subcategory', [id])
            return JsonResponse({'message': 'Category deleted successfully', 'category_id:': id})
        except Exception as e:
            return JsonResponse({'error': 'Failed to delete category', 'exception': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        status = request.POST.get('status') == '1'
        modules = request.POST.getlist('modules')
        created_by = int(request.user.id)
        created_date = datetime.now()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT add_user(%s, %s, %s, %s, %s, %s);",
                [username, password, status, modules, created_by, created_date]
            )
            user_id = cursor.fetchone()[0]
            print(user_id)
        return redirect('add_user')
    else:
        # Fetch employee names from the employee table
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM employee")
            employees = cursor.fetchall()

        employee_names = [employee[0] for employee in employees]

        username = None
        if request.user.is_authenticated:
            username = request.user.username
        return render(request, 'product_tracking/user.html', {'username': username, 'employee_names': employee_names})


@login_required
def user_list(request):
    print('Received data:', {})
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM getuser()")
        rows = cursor.fetchall()
        print("fetched user list")

    user_listing = []
    for row in rows:
        created_date_time = row[6].strftime('%d-%m-%Y')
        user_listing.append({
            'user_id': row[0],
            'user_name': row[1],
            'password': row[2],
            'status': row[3],
            'modules': row[4],
            'created_by': row[5],
            'created_date_time': created_date_time
        })
        print(user_listing)
    return JsonResponse(user_listing, safe=False)


@login_required
def update_user(request, user_id):  # noqa
    if request.method == 'POST':
        user_id = request.POST.get('userId')
        user_name = request.POST.get('username')
        password = request.POST.get('password')
        status = request.POST.get('statusText')
        modules = request.POST.getlist('modules')

        print('Received data:', modules)

        try:
            with connection.cursor() as cursor:
                print('inside the object')
                cursor.callproc('update_user', [user_id, user_name, password, status, modules])
                # user_id = cursor.fetchone()[0]  # noqa
                print('updated modules: ', modules)
                cursor.execute("COMMIT;")
                print('updated')
            return JsonResponse(
                {'message': 'User details updated successfully', 'user_id': user_id})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'})


@login_required
def delete_user(request, id):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.callproc('deleteuser', [id])
            return JsonResponse({'message': 'User deleted successfully', 'User_id:': id})
        except Exception as e:
            return JsonResponse({'error': 'Failed to delete User', 'exception': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def add_employee(request):
    print('inside the add employee function')
    if request.method == 'POST':
        print('inside the POST method')
        # Extract form data
        employee_id = request.POST.get('employee_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        designation = request.POST.get('designation')
        mobile_no = request.POST.get('mobile_no')
        gender = request.POST.get('gender')
        joining_date = request.POST.get('joining_date')
        dob = request.POST.get('dob')
        reporting = request.POST.get('reporting')
        p_address = request.POST.get('p_address')
        c_address = request.POST.get('c_address')
        country = request.POST.get('country')
        state = request.POST.get('state')
        status = request.POST.get('status')
        created_by = request.user.id
        created_date = datetime.now()
        profile_photo = request.FILES.get('profile_photo')
        attachment_images = request.FILES.getlist('attachments[]')

        # Define the upload directory
        upload_dir = 'C:/Users/vandana ajara/Desktop/New folder/wms2/wms2/product_tracking/media/uploads'
        os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists

        # Process attachment images
        image_paths = []
        for image in attachment_images:
            if image:
                image_path = os.path.join(upload_dir, image.name)
                with open(image_path, 'wb') as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                image_paths.append(image_path)
            else:
                image_paths.append(None)

        # Process profile photo
        profile_photo_path = None
        if profile_photo:
            profile_photo_path = os.path.join(upload_dir, profile_photo.name)
            with open(profile_photo_path, 'wb') as f:
                for chunk in profile_photo.chunks():
                    f.write(chunk)

        # Call the stored procedure/function
        with connection.cursor() as cursor:
            print('inside the stored procedure function')
            cursor.callproc('add_employee', [
                employee_id, name, email, password, designation, mobile_no, gender, joining_date, dob, reporting,
                p_address, c_address, country, state, status, created_by, created_date,
                profile_photo_path, *image_paths  # Pass paths to the stored procedure
            ])
        return redirect('add_employee')

    return render(request, 'product_tracking/employee.html')


@login_required
def employee_dropdown(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, name FROM get_employee_details()')
            employees = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
            print('Employees fetched successfully:', employees)
            return JsonResponse({'employees': employees}, safe=False)
    except Exception as e:
        print("Error fetching employees:", e)
        return JsonResponse({'employees': []})


@login_required
def employee_list(request):
    print('Received data:')
    employee_listing = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM get_employee_details()")
            rows = cursor.fetchall()
            print("fetched employee list")

            for row in rows:
                created_date = row[16]
                employee_listing.append({
                    'id': row[0],
                    'employee_id': row[1],
                    'name': row[2],
                    'email': row[3],
                    'password': row[4],
                    'designation': row[5],
                    'mobile_no': row[6],
                    'gender': row[7],
                    'joining_date': row[8],
                    'dob': row[9],
                    'p_address': row[11],
                    'c_address': row[12],
                    'country': row[13],
                    'status': row[14],
                    'created_by': row[15],
                    'images': row[17],  # Path to the image
                    'created_date': created_date
                })

                print(row[17])
    except Exception as e:
        print("Error fetching employee list:", e)
    return JsonResponse(employee_listing, safe=False)



