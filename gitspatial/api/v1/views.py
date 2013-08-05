from django.shortcuts import HttpResponse


def feature_set_query(request, user_name=None, repo_name=None, feature_set_name=None):
    return HttpResponse('User is {user}. Repo is {repo}. Feature Set is {feature_set}.'.format(user=user_name, repo=repo_name, feature_set=feature_set_name))
