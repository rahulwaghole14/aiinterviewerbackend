from interviews.models import Interview

print('Status Values:')
print(f'Interview.Status.SCHEDULED = {repr(Interview.Status.SCHEDULED)}')
print(f'Interview.Status.SCHEDULED.value = {repr(Interview.Status.SCHEDULED.value)}')
print(f'String "scheduled" = {repr("scheduled")}')
print(f'Match: {Interview.Status.SCHEDULED.value == "scheduled"}')
