from django.shortcuts import render, redirect
from django.contrib import messages
import bcrypt

from .models import User, Category, Job

def login_reg_page(request):
    return render(request, 'login_reg.html')

def create_user(request):
    potential_users = User.objects.filter(email = request.POST['email'])

    if len(potential_users) != 0:
        messages.error(request, "User with that email already exists!")
        return redirect('/')

    errors = User.objects.basic_validator(request.POST)

    if len(errors) > 0:
        for key, val in errors.items():
            messages.error(request, val)
        return redirect('/')

    hashed_pw = bcrypt.hashpw(request.POST["password"].encode(), bcrypt.gensalt()).decode()

    new_user = User.objects.create(
        first_name = request.POST['first_name'],
        last_name = request.POST['last_name'],
        email = request.POST['email'],
        password = hashed_pw,
    )

    request.session['user_id'] = new_user.id

    return redirect('/dashboard')

def login(request):
    potential_users = User.objects.filter(email = request.POST['email'])

    if len(potential_users) == 0:
        messages.error(request, "Please check your email and password.")
        return redirect('/')

    user = potential_users[0]

    if not bcrypt.checkpw(request.POST['password'].encode(), user.password.encode()):
        messages.error(request, "Please check your email and password.")
        return redirect('/')

    request.session['user_id'] = user.id

    return redirect('/dashboard')

def logout(request):
    if 'user_id' not in request.session:
        messages.error(request, "You are not logged in!")
        return redirect('/')

    request.session.clear()

    return redirect('/')

def dashboard_page(request):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')
        
    current_user = User.objects.get(id=request.session['user_id'])
    current_user_added_jobs = current_user.added_jobs.all()
    all_jobs = Job.objects.exclude(id__in=current_user_added_jobs)

    context = {
        'current_user': current_user,
        'all_jobs': all_jobs,
        'users_added_jobs': current_user_added_jobs,
    }

    return render(request, 'dashboard.html', context)

def add_job_page(request):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')
        
    current_user = User.objects.get(id=request.session['user_id'])
    category_options = Category.objects.all().order_by('-created_at')

    context = {
        'current_user': current_user,
        'category_options': category_options
    }

    return render(request, 'add_job.html', context)

def create_job(request):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')

    current_user = User.objects.get(id=request.session['user_id'])

    job_errors = Job.objects.basic_validator(request.POST)

    if len(Category.objects.filter(category = request.POST['category_text'])) != 0:
        messages.error(request, "The category you typed already exists. Please check from list.")
        return redirect('/jobs/add')

    if len(job_errors) > 0:
        for key, val in job_errors.items():
            messages.error(request, val)
        return redirect('/jobs/add')

    new_job = Job.objects.create(
        title = request.POST['title'],
        description = request.POST['description'],
        location = request.POST['location'],
        created_by_user = current_user,
    )

    if request.POST['category_text'] != "":
        new_category = Category.objects.create(category = request.POST['category_text'])
        new_job.categories.add(new_category)

    if request.POST.getlist('category') != []:
        for category_id in request.POST.getlist('category'):
            category = Category.objects.get(id = category_id)
            category.jobs.add(new_job)

    return redirect('/dashboard')

def edit_job_page(request, job_id):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')

    current_user = User.objects.get(id=request.session['user_id'])
    current_job = Job.objects.get(id = job_id)
    all_categories = Category.objects.all()

    if current_job.created_by_user != current_user:
        messages.error(request, "You have not created this job. You cannot edit it!")
        return redirect('/dashboard')

    context = {
        "current_user": current_user,
        "current_job": current_job,
        "all_categories": all_categories,
    }

    return render(request, 'edit_job.html', context)

def update_job(request, job_id):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')

    current_user = User.objects.get(id=request.session['user_id'])
    current_job = Job.objects.get(id = job_id)

    if len(Category.objects.filter(category = request.POST['category_text'])) != 0:
        messages.error(request, "The category you typed already exists. Please check from list.")
        return redirect(f'/jobs/{job_id}/edit')

    if current_job.created_by_user != current_user:
        messages.error(request, "You have not created this job. You cannot edit it!")
        return redirect('/dashboard')

    job_errors = Job.objects.basic_validator(request.POST)

    if len(job_errors) > 0:
        for key, val in job_errors.items():
            messages.error(request, val)
        return redirect(f'/jobs/{job_id}/edit')

    for category in Category.objects.exclude(id__in = request.POST.getlist('category')):
        current_job.categories.remove(category)

    if request.POST['category_text'] != "":
        new_category = Category.objects.create(category = request.POST['category_text'])
        current_job.categories.add(new_category)

    for category_id in request.POST.getlist('category'):
        category = Category.objects.get(id = category_id)
        category.jobs.add(current_job)

    

    current_job.title = request.POST['title']
    current_job.description = request.POST['description']
    current_job.location = request.POST['location']
    current_job.save()

    return redirect('/dashboard')

def view_job_page(request, job_id):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')

    current_user = User.objects.get(id=request.session['user_id'])
    current_job = Job.objects.get(id = job_id)
    all_categories = Category.objects.all().order_by('category')

    current_user_added_jobs = current_user.added_jobs.all()
    all_jobs = Job.objects.exclude(id__in=current_user_added_jobs)

    category_empty = True

    if len(current_job.categories.all()) != 0:
        category_empty = False

    context = {
        'current_user': current_user,
        'all_jobs': all_jobs,
        'current_user_added_jobs': current_user_added_jobs,
        'current_job': current_job,
        'all_categories': all_categories,
        'category_empty': category_empty
    }

    return render(request, 'view_job.html', context)

def delete_job(request, job_id):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')

    current_user = User.objects.get(id=request.session['user_id'])
    current_job = Job.objects.get(id = job_id)

    if current_job.created_by_user != current_user:
        messages.error(request, "You have not created this job. You cannot remove it!")
        return redirect('/dashboard')

    current_job.delete()

    return redirect('/dashboard')

def add_job_to_user(request, job_id):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')

    current_user = User.objects.get(id=request.session['user_id'])
    current_job = Job.objects.get(id = job_id)

    current_user.added_jobs.add(current_job)

    return redirect('/dashboard')

def remove_job_from_user(request, job_id):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')

    current_user = User.objects.get(id=request.session['user_id'])
    current_job = Job.objects.get(id = job_id)

    current_user.added_jobs.remove(current_job)

    return redirect('/dashboard')

def done_job(request, job_id):
    if 'user_id' not in request.session:
        messages.error(request, "Must be logged in!")
        return redirect('/')

    current_user = User.objects.get(id=request.session['user_id'])
    current_job = Job.objects.get(id = job_id)

    if current_user not in current_job.added_users.all():
        messages.error(request, "You have not added this job. You cannot finish it!")
        return redirect('/dashboard')

    current_job.delete()

    return redirect('/dashboard')