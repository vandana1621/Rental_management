import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.models import User
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
import os

from django.views.decorators.csrf import csrf_exempt
from psycopg2 import IntegrityError

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
        status = request.POST.get('status') == '1'
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
    page = int(request.GET.get('page', 1))
    page_size = 10
    offset = (page - 1) * page_size

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM master_category")
        total_items = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM get_category_details() LIMIT %s OFFSET %s", [page_size, offset])
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

    return JsonResponse({
        'categories': category_listing,
        'total_items': total_items,
        'current_page': page
    }, safe=False)


@login_required
@csrf_exempt
def update_category(request, category_id):
    if request.method == 'POST':
        print('Received POST request to update category details')

        # Extract the form data
        category_name = request.POST.get('categoryName')
        category_description = request.POST.get('categoryDescription', '')
        status = request.POST.get('statusText') == 'true' or request.POST.get(
            'statusText') == 'True' or request.POST.get('statusText') == '1'

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
                {'success': True, 'message': 'Category details updated successfully',
                 'updated_category_id': updated_category_id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Failed to update category details', 'exception': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})


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
        return render(request, 'product_tracking/sub-performance1.html',
                      {'username': username, 'categories': categories})


# def subcategory_list(request, category_id):
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT * FROM get_sub(%s)", [category_id])
#         rows = cursor.fetchall()
#
#     subcategory_listing = []
#     for row in rows:
#         created_date = row[5].strftime('%d-%m-%Y')
#         subcategory_listing.append({
#             'id': row[0],
#             'category_name': row[1],
#             'name': row[2],
#             'status': row[3],
#             'created_by': row[4],
#             'created_date': created_date
#         })
#         print('Sub Category show successfully', subcategory_listing)
#     return JsonResponse(subcategory_listing, safe=False)

@login_required
def subcategory_list(request, category_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM get_sub(%s)", [category_id])
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

    context = {
        'subcategories': json.dumps(subcategory_listing),  # Ensure JSON is correctly formatted
        'category_id': category_id
    }
    return render(request, 'product_tracking/sub-performance1.html', context)


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


@login_required
def add_equipment(request):
    if request.method == 'POST':
        equipment_name = request.POST.get('equipment_name')
        subcategory_name = request.POST.get('subcategory_name')
        category_name = request.POST.get('category_name')
        type = request.POST.get('type')
        dimension_h = request.POST.get('dimension_h')
        dimension_w = request.POST.get('dimension_w')
        dimension_l = request.POST.get('dimension_l')
        weight = request.POST.get('weight')
        volume = request.POST.get('volume')
        hsn_no = request.POST.get('hsn_no')
        country_origin = request.POST.get('country_origin')
        attachment = request.FILES.get('attachment')
        status = request.POST.get('status')
        created_by = request.user.id
        created_date = datetime.now()

        # Save image to the desired location
        attachment_path = None
        if attachment:
            attachment_path = os.path.join(settings.MEDIA_ROOT, 'attachments', attachment.name)
            os.makedirs(os.path.dirname(attachment_path), exist_ok=True)  # Ensure the directory exists
            with open(attachment_path, 'wb') as f:
                for chunk in attachment.chunks():
                    f.write(chunk)

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT public.add_equipment_list(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    );
                    """,
                    [
                        equipment_name,
                        subcategory_name,
                        category_name,
                        type,
                        dimension_h,
                        dimension_w,
                        dimension_l,
                        weight,
                        volume,
                        hsn_no,
                        country_origin,
                        attachment_path if attachment else None,
                        status,
                        created_by,
                        created_date
                    ]
                )
                return redirect(f'/equipment_list/?subcategory_id={subcategory_name}')
        except IntegrityError as e:
            error_message = str(e)
            if 'duplicate key value violates unique constraint "unique_equipment_name"' in error_message:
                error_message = 'Equipment name already exists. Please choose a different name.'
            print("An unexpected error occurred:", error_message)
            return render(request, 'product_tracking/index.html', {'error': error_message})
        except Exception as e:
            print("An unexpected error occurred:", e)
            return render(request, 'product_tracking/index.html', {'error': 'An unexpected error occurred'})
    else:
        username = None
        if request.user.is_authenticated:
            username = request.user.username
        return render(request, 'product_tracking/Equipment.html', {'username': username})


@login_required
def insert_vendor(request):
    if request.method == 'POST':
        # Retrieve form data
        vendor_name = request.POST.get('vendor_name')
        purchase_date = request.POST.get('purchase_date')
        unit_price = request.POST.get('unit_price')
        rental_price = request.POST.get('rental_price')
        reference_no = request.POST.get('reference_no')
        attachment = request.FILES.get('attachment')
        unit = request.POST.get('unitValue')
        # Extract dynamically generated input box values
        serial_numbers = []
        barcode_numbers = []
        for i in range(1, int(unit) + 1):
            serial_number = request.POST.get(f'serialNumber{i}', '')
            barcode_number = request.POST.get(f'barcodeNumber{i}', '')
            serial_numbers.append(serial_number)
            barcode_numbers.append(barcode_number)

        equipment_id = request.POST.get('equipmentId')
        subcategory_id = None
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT sub_category_id FROM equipment_list WHERE id = %s",
                    [equipment_id]
                )
                subcategory_id = cursor.fetchone()[0]
        except Exception as e:
            print(f"An unexpected error occurred while fetching equipment ID: {e}")

        attachment_path = None
        if attachment:
            attachment_path = os.path.join(settings.MEDIA_ROOT, 'attachments', attachment.name)
            os.makedirs(os.path.dirname(attachment_path), exist_ok=True)  # Ensure the directory exists
            with open(attachment_path, 'wb') as f:
                for chunk in attachment.chunks():
                    f.write(chunk)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT add_stock(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                    [equipment_id, vendor_name, purchase_date, unit_price, rental_price, reference_no, attachment_path,
                     unit, serial_numbers, barcode_numbers]
                )
            print('Stock Details added successfully')
            return redirect(f'/equipment_list/?subcategory_id={subcategory_id}')
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return render(request, 'product_tracking/index.html', {'error': 'An unexpected error occurred'})
    else:
        # Handle GET request
        username = None
        if request.user.is_authenticated:
            username = request.user.username
        return render(request, 'product_tracking/performance.html', {'username': username})


@login_required
def subcategory_dropdown(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, category_name, name FROM get_sub()')
            subcategories = [{'id': row[0], 'category_name': row[1], 'name': row[2]} for row in cursor.fetchall()]
            print('sub category fetched successfully:', subcategories)
            return JsonResponse({'subcategories': subcategories}, safe=False)
    except Exception as e:
        # Handle exceptions, maybe log the error for debugging
        print("Error fetching sub category:", e)
        return JsonResponse({'subcategories': []})


@login_required
def get_category_name(request):
    try:
        subcategory_id = request.GET.get('subcategory_id')
        # Fetch category name based on subcategory_id
        with connection.cursor() as cursor:
            cursor.execute('SELECT category_name FROM get_sub() WHERE id = %s', [subcategory_id])
            row = cursor.fetchone()
            category_name = row[0] if row else None
        return JsonResponse({'category_name': category_name})
    except Exception as e:
        # Handle exceptions, maybe log the error for debugging
        print("Error fetching category name:", e)
        return JsonResponse({'category_name': None})


@login_required
def subcategory_list(request, category_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM get_sub(%s)", [category_id])
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

    context = {
        'subcategories': json.dumps(subcategory_listing),  # Ensure JSON is correctly formatted
        'category_id': category_id
    }
    return render(request, 'product_tracking/sub-performance1.html', context)


@login_required
def equipment_list(request):
    subcategory_id = request.GET.get('subcategory_id')
    if not subcategory_id:
        return JsonResponse({'error': 'Missing subcategory_id parameter'}, status=400)

    equipment_listing = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM get_equipment_list(%s)", [subcategory_id])
            rows = cursor.fetchall()

            for row in rows:
                created_date = row[15].strftime('%d-%m-%Y')
                equipment_listing.append({
                    'id': row[0],
                    'equipment_name': row[1],
                    'sub_category_name': row[2],
                    'category_type': row[3],
                    'type': row[4],
                    'dimension_height': row[5],
                    'dimension_width': row[6],
                    'dimension_length': row[7],
                    'weight': row[8],
                    'volume': row[9],
                    'hsn_no': row[10],
                    'country_origin': row[11],
                    'attachment': row[12],
                    'status': row[13],
                    'created_by': row[14],
                    'created_date': created_date
                })
    except Exception as e:
        print("Error fetching equipment list:", e)
        return JsonResponse({'error': str(e)}, status=500)

    context = {
        'equipment_listing': json.dumps(equipment_listing),
        'subcategory_id': subcategory_id
    }
    return render(request, 'product_tracking/Equipment.html', context)


@login_required
def delete_equipment_list(request, id):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.callproc('delete_equipment', [id])
            return JsonResponse({'message': 'Equipment deleted successfully', 'Equipment_id:': id})
        except Exception as e:
            return JsonResponse({'error': 'Failed to delete Equipment', 'exception': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def update_equipment(request, id):
    if request.method == 'POST':
        print('Received POST request to update employee details')

        # Extract the form data
        name = request.POST.get('employeeName')
        sub_category_name = request.POST.get('subCategory')
        category_type = request.POST.get('categoryType')
        equipment_type = request.POST.get('equipmentType')
        dimension_height = request.POST.get('dimensionHeight')
        dimension_width = request.POST.get('dimensionWidth')
        dimension_length = request.POST.get('dimensionLength')
        weight = request.POST.get('weight')
        volume = request.POST.get('volume')
        hsn_no = request.POST.get('hsnNo')
        country = request.POST.get('employeeCountry')
        status = request.POST.get('statusText')

        print(id, name, sub_category_name, country, status)
        try:
            print('inside the try block')
            with connection.cursor() as cursor:
                print('inside the cursor')
                cursor.callproc('update_equipment',
                                [id, name, sub_category_name, category_type, equipment_type, dimension_height,
                                 dimension_width, dimension_length, weight, volume, hsn_no, country, status])
                print('inside the callproc', id)
                updated_employee_id = cursor.fetchone()[0]
                print(updated_employee_id)
            return JsonResponse(
                {'message': 'Employee details updated successfully', 'updated_employee_id': updated_employee_id})
        except Exception as e:
            return JsonResponse({'error': 'Failed to update employee details', 'exception': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'})


@login_required
def edit_subcategory_dropdown(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, category_name, name FROM get_sub()')
            sub = [{'id': row[0], 'category_name': row[1], 'name': row[2]} for row in cursor.fetchall()]
            print('sub category fetched successfully:', sub)
            return JsonResponse({'sub': sub}, safe=False)
    except Exception as e:
        # Handle exceptions, maybe log the error for debugging
        print("Error fetching sub category:", e)
        return JsonResponse({'sub': []})


@login_required
def edit_get_category_name(request):
    try:
        subcategory_id = request.GET.get('subcategory_id')
        # Fetch category name based on subcategory_id
        with connection.cursor() as cursor:
            cursor.execute('SELECT category_name FROM get_sub() WHERE id = %s', [subcategory_id])
            row = cursor.fetchone()
            category_name = row[0] if row else None
        return JsonResponse({'category_name': category_name})
    except Exception as e:
        # Handle exceptions, maybe log the error for debugging
        print("Error fetching category name:", e)
        return JsonResponse({'category_name': None})


def fetch_stock_status(request, equipment_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM get_stock_status(%s)", [equipment_id])
        stock_data = cursor.fetchone()
        print('Equipment ID:', equipment_id)
        print('Equipment ID:', equipment_id, stock_data)

    if stock_data is not None:
        unit_count = stock_data[0]
        stock_status = 'Stock in completed' if unit_count > 0 else 'Stock in pending'
    else:
        unit_count = 0
        stock_status = 'Stock in pending'
    return JsonResponse({'unit_count': unit_count, 'stock_status': stock_status})


def fetch_serial_barcode_no(request, equipment_id):
    # Execute the PostgreSQL function
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM get_serial_barcode_no(%s)", [equipment_id])
        rows = cursor.fetchall()
        if rows:
            # If multiple rows are returned, create a list of dictionaries
            data = [{'serial_number': row[0], 'barcode_number': row[1]} for row in rows]
        else:
            # If no rows are returned, return an error
            return JsonResponse({'error': 'No data found for equipment ID ' + str(equipment_id)}, status=404)

    return JsonResponse(data, safe=False)


def get_dimension_list(request, equipment_id):
    print('inside the function')
    # Execute the PostgreSQL function
    with connection.cursor() as cursor:
        print('inside the object of cursor')
        cursor.execute("SELECT * FROM get_dimension_list_stock(%s)", [equipment_id])
        rows = cursor.fetchall()  # Fetch all rows
        print('row values:', rows)
        if rows:
            # Initialize dictionaries to hold single and aggregated data
            dimension_details = {}
            stock_details = {
                'vender_name': '',
                'purchase_date': '',
                'unit_price': '',
                'rental_price': '',
                'reference_no': '',
                'unit': '',
                'serial_no': [],
                'barcode_no': []
            }

            # Extract common dimension details from the first row
            first_row = rows[0]
            dimension_details = {
                'dimension_height': first_row[0] or '',
                'dimension_width': first_row[1] or '',
                'dimension_length': first_row[2] or '',
                'weight': first_row[3] or '',
                'volume': first_row[4] or '',
                'hsn_no': first_row[5] or '',
                'country_origin': first_row[6] or '',
                'status': first_row[7] or '',
                'created_by': first_row[8] or '',
                'created_date': first_row[9].strftime('%d-%m-%Y') if first_row[9] else ''
            }

            # Check if any row has serial numbers or barcode numbers
            has_stock_details = any(row[16] or row[17] for row in rows)

            if has_stock_details:
                # Aggregate serial numbers and barcode numbers
                for row in rows:
                    stock_details['serial_no'].append(row[16] or '')
                    stock_details['barcode_no'].append(row[17] or '')

                # Assign single values to stock_details
                stock_details['vender_name'] = first_row[10] or ''
                stock_details['purchase_date'] = first_row[11].strftime('%d-%m-%Y') if first_row[11] else ''
                stock_details['unit_price'] = first_row[12] or ''
                stock_details['rental_price'] = first_row[13] or ''
                stock_details['reference_no'] = first_row[14] or ''
                stock_details['unit'] = first_row[15] or ''

            # Merge dictionaries
            data = {**dimension_details, **stock_details}
            print('Values are shown in the table are:', data)
        else:
            # If no rows are returned, return an error
            return JsonResponse({'error': 'No data found for equipment ID ' + str(equipment_id)}, status=404)

    return JsonResponse(data)

@login_required()
def Stock_list(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return render(request, 'product_tracking/stocks.html', {'username': username})


@login_required
def fetch_equipment_list(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_type', '')
        start = int(request.POST.get('start', 0))
        limit = int(request.POST.get('limit', 10))

        print(f"Fetching data for category: {category_id}, start: {start}, limit: {limit}")

        # Fetch paginated data
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM public.get_list(%s) OFFSET %s LIMIT %s
            """, [category_id, start, limit])
            rows = cursor.fetchall()
            print(f"Fetched rows: {rows}")

        # Fetch total count
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT el.equipment_name, el.sub_category_id, el.category_type
                    FROM public.equipment_list el
                    LEFT JOIN public.sub_category sc ON el.sub_category_id = sc.id
                    LEFT JOIN public.stock_details sd ON el.id = sd.equipment_id
                    WHERE sc.category_id = %s
                ) AS distinct_items
            """, [category_id])
            total_items = cursor.fetchone()[0]
            print(f"Total items: {total_items}")

        equipment_list = []
        for row in rows:
            equipment_list.append({
                'equipment_name': row[0],
                'sub_category_name': row[1],  # Ensure this is the correct index for sub_category_name
                'category_type': row[2],
                'unit_price': row[3],
                'rental_price': row[4],
                'total_units': row[5],
            })

        print(f"Equipment list: {equipment_list}")

        return JsonResponse({'totalItems': total_items, 'data': equipment_list}, safe=False)
    else:
        return JsonResponse({'error': 'Invalid request'})