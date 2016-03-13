# -*- coding:utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse

from .forms import RegistrationForm
 
def registrate(request):
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            return HttpResponse('Форма верна!')
    else:
        form = RegistrationForm()
    return render(request, 'registrate.html', {'form': form})