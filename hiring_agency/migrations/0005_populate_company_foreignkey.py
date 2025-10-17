# Generated manually
from django.db import migrations


def populate_company_foreignkey(apps, schema_editor):
    """
    Populate the new company ForeignKey field based on existing company_name values
    """
    UserData = apps.get_model("hiring_agency", "UserData")
    Company = apps.get_model("companies", "Company")

    # Get all UserData records that have a company_name but no company ForeignKey
    user_data_records = UserData.objects.filter(company_name__isnull=False).exclude(
        company_name=""
    )

    for user_data in user_data_records:
        if user_data.company_name:
            # Try to find the company by name (use first() to handle duplicates)
            company = Company.objects.filter(name=user_data.company_name).first()
            if company:
                user_data.company = company
                user_data.save()
                print(f"Updated UserData {user_data.id} with company {company.name}")
            else:
                # If company doesn't exist, create it
                company = Company.objects.create(
                    name=user_data.company_name,
                    description=f"Auto-created from hiring agency data for {user_data.company_name}",
                    is_active=True,
                )
                user_data.company = company
                user_data.save()
                print(
                    f"Created company {company.name} and linked to UserData {user_data.id}"
                )


def reverse_populate_company_foreignkey(apps, schema_editor):
    """
    Reverse the migration by clearing the company ForeignKey field
    """
    UserData = apps.get_model("hiring_agency", "UserData")
    UserData.objects.update(company=None)


class Migration(migrations.Migration):
    dependencies = [
        ("hiring_agency", "0004_userdata_company"),
        ("companies", "0002_company_email_company_password"),
    ]

    operations = [
        migrations.RunPython(
            populate_company_foreignkey, reverse_populate_company_foreignkey
        ),
    ]
