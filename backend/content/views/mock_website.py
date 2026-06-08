from django.shortcuts import get_object_or_404, render

from content.models import MockOpportunity


def mock_list(request):
    opportunities = MockOpportunity.objects.all()
    return render(request, "content/mock_website_list.html", {"opportunities": opportunities})


def mock_detail(request, pk):
    opportunity = get_object_or_404(MockOpportunity, pk=pk)
    return render(request, "content/mock_website_detail.html", {"opportunity": opportunity})
