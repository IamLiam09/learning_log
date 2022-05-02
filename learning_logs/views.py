from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Topic, Entry
from .forms import TopicForm, EntryForm
from django.http import Http404
from django.db.models import Q
# Create your views here.
def index(request):
    """The homepage for learning log."""
    return render(request, 'learning_logs/index.html')

def _get_topics_for_user(user):
    """return a queryset of topics and the user can access."""
    q = Q(public=True)
    #if django "user.is_authenticated()" (with parens)
    if user.is_authenticated:
        #adds user's own private topics to the query
        q = q | Q(public=False, owner=user)
    return Topic.objects.filter(q)

def topics(request):
    """Show all topics"""
    topics = _get_topics_for_user(request.user).order_by('date_added')
    context = {'topics': topics}
    return render(request, 'learning_logs/topics.html', context)

@login_required
def topic(request, topic_id):
    """show a simple topic and all it's entries"""
    topics = _get_topics_for_user(request.user)
    # here we're passing the filtered queryset, so
    # if the topic "topic_id" is private and the user is with
    #anonymos or not the topic owner, it will raise a 404
    topic = get_object_or_404(Topic, id=topic_id)
    #Make sure the topic belongs to the current user
    check_topic_owner(topic.owner, request)
    entries = topic.entry_set.order_by('-date_added')
    context = {'topic': topic, 'entries':entries}
    return render(request, 'learning_logs/topic.html', context,)

@login_required
def new_topic(request):
    """Add a new topic."""
    if request.method != 'POST':
        #No data submitted;create a blank form.
        form = TopicForm()
    else:
        # POST data submitted; process data.
        form = TopicForm(data=request.POST)
        if form.is_valid():
            new_topic = form.save(commit=False)
            new_topic.owner = request.user
            new_topic.save()
            return redirect('learning_logs:topics')
    #Display a blank or invalid form.
    context = {'form': form}
    return render(request, 'learning_logs/new_topic.html', context)

@login_required
def new_entry(request, topic_id):
    """Add a new entry for a particular Topic."""
    topic = get_object_or_404(Topic, id=topic_id)
    check_topic_owner(topic.owner, request)
    if request.method != 'POST':
        #NO data sumbitted create a blank form.
        form = EntryForm()
    else:
        #Post data submitted, process data.
        form = EntryForm(data=request.POST)
        if form.is_valid():
            new_entry = form.save(commit=False)
            new_entry.topic = topic
            new_entry.save()
            return redirect('learning_logs:topic', topic_id=topic_id)
    #Display a blank or invalid form.
    context = {'topic': topic, 'form': form}
    return render(request, 'learning_logs/new_entry.html', context)

@login_required
def edit_entry(request, entry_id):
    """Edit an exiting entry."""
    entry = get_object_or_404(Entry, id=entry_id)
    topic = entry.topic
    check_topic_owner(topic.owner, request)
    if request.method != 'POST':
        #Intial request; pre-fill form with the current entry.
        form = EntryForm(instance=entry)
    else:
        # Post data submitted;process data
        form = EntryForm(instance=entry, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('learning_logs:topic', topic_id=topic.id)
    context = {'entry': entry, 'topic': topic, 'form': form}
    return render(request, 'learning_logs/edit_entry.html', context)
def check_topic_owner(owner, request):
    if owner != request.user:
        raise Http404