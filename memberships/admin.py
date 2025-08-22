from django.contrib import admin

from .models import *

admin.site.register(Membership)
admin.site.register(MembershipType)
admin.site.register(Institution)
admin.site.register(EducationLevel)
admin.site.register(PersonalInfo)
admin.site.register(ContactInfo)
admin.site.register(EducationInfo)
admin.site.register(WorkInfo)
admin.site.register(WorkflowLog)

