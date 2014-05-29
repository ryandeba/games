from django.shortcuts import render

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def index(request):
  return render(request, 'common/index.html', {'username': request.user.username})

def register(request):
  username = request.POST['username']
  password = request.POST['password']

  User.objects.create_user(username = username, password = password)
  user = authenticate(username = username, password = password)
  if user is not None:
    login(request, user)
  return redirect('/')
