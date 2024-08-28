from django.db import models
from django.conf import settings


class ContactList(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contact_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Contact(models.Model):
    contact_list = models.ForeignKey(ContactList, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    company_size = models.IntegerField(default=0, null=True, blank=True)
    industry = models.CharField(default='Technology', max_length=100, blank=True)
    location = models.CharField(default='London', max_length=100, blank=True)
    technology_stack = models.TextField(default='Python', blank=True)
    budget = models.DecimalField(default=5000, max_digits=10, decimal_places=2, null=True, blank=True)
    decision_maker_role = models.CharField(default='VP', max_length=100, blank=True)
    pain_points = models.TextField(default='efficiency', blank=True)
    previous_engagement = models.TextField(default='demo', blank=True)
    icp_score = models.FloatField(default=0)
    
    def calculate_icp_score(self):
        weights = {
            'company_size': 0.2,
            'industry': 0.15,
            'location': 0.1,
            'technology_stack': 0.15,
            'budget': 0.2,
            'decision_maker_role': 0.1,
            'pain_points': 0.05,
            'previous_engagement': 0.05
        }
    
        scores = {
            'company_size': self.score_company_size(),
            'industry': self.score_industry(),
            'location': self.score_location(),
            'technology_stack': self.score_technology_stack(),
            'budget': self.score_budget(),
            'decision_maker_role': self.score_decision_maker_role(),
            'pain_points': self.score_pain_points(),
            'previous_engagement': self.score_previous_engagement()
        }
    
        weighted_scores = [weights[attr] * scores[attr] for attr in weights]
        self.icp_score = sum(weighted_scores) / sum(weights.values())
        self.save()
    
    def score_company_size(self):
        if not self.company_size:
            return 0
        elif self.company_size < 10:
            return 1
        elif 10 <= self.company_size < 50:
            return 2
        elif 50 <= self.company_size < 200:
            return 3
        elif 200 <= self.company_size < 1000:
            return 4
        else:
            return 5
    
    def score_industry(self):
        target_industries = ['Technology', 'Healthcare', 'Finance']
        return 5 if self.industry in target_industries else 1
    
    def score_location(self):
        target_locations = ['New York', 'San Francisco', 'London']
        return 5 if any(location in self.location for location in target_locations) else 1
    
    def score_technology_stack(self):
        preferred_technologies = ['Python', 'JavaScript', 'AWS']
        score = sum(1 for tech in preferred_technologies if tech.lower() in self.technology_stack.lower())
        return min(score, 5)
    
    def score_budget(self):
        if not self.budget:
            return 0
        elif self.budget < 10000:
            return 1
        elif 10000 <= self.budget < 50000:
            return 2
        elif 50000 <= self.budget < 100000:
            return 3
        elif 100000 <= self.budget < 500000:
            return 4
        else:
            return 5
    
    def score_decision_maker_role(self):
        target_roles = ['CEO', 'CTO', 'VP', 'Director']
        return 5 if any(role.lower() in self.decision_maker_role.lower() for role in target_roles) else 1
    
    def score_pain_points(self):
        key_pain_points = ['cost reduction', 'efficiency', 'scalability']
        score = sum(1 for point in key_pain_points if point.lower() in self.pain_points.lower())
        return min(score, 5)
    
    def score_previous_engagement(self):
        engagement_keywords = ['meeting', 'demo', 'trial']
        score = sum(1 for keyword in engagement_keywords if keyword.lower() in self.previous_engagement.lower())
        return min(score, 5)