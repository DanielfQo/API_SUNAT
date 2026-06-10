from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.credentials.models import SunatCredential

class Command(BaseCommand):
    help = "Puebla la base de datos con un superusuario, una empresa de prueba, una aplicación cliente y credenciales para el MVP"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== SEEDING DATABASE FOR API SUNAT MVP ==="))

        # 1. Crear Superusuario
        username = "admin"
        email = "admin@test.com"
        password = "admin123"

        user, user_created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True}
        )
        if user_created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}' with password '{password}'"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists"))

        # 2. Crear Empresa
        ruc = "20123456789"
        business_name = "Empresa Test SAC"
        company, company_created = Company.objects.get_or_create(
            ruc=ruc,
            defaults={"business_name": business_name, "owner": user}
        )
        if company_created:
            self.stdout.write(self.style.SUCCESS(f"Created company '{business_name}' (RUC: {ruc}) owned by '{username}'"))
        else:
            # Asegurar que el dueño está asignado incluso si la empresa ya existe
            company.owner = user
            company.save()
            self.stdout.write(self.style.WARNING(f"Company '{business_name}' already exists. Assigned owner '{username}'"))

        # 3. Crear ClientApp
        app, app_created = ClientApp.objects.get_or_create(
            company=company,
            name="ERP Principal",
            defaults={"is_active": True}
        )
        if app_created:
            self.stdout.write(self.style.SUCCESS(f"Created Client App '{app.name}'"))
        else:
            self.stdout.write(self.style.WARNING(f"Client App '{app.name}' already exists"))

        # Mostrar claves de salida
        self.stdout.write(self.style.SUCCESS("--------------------------------------------------"))
        self.stdout.write(self.style.SUCCESS("API AUTHENTICATION CREDENTIALS:"))
        self.stdout.write(self.style.SUCCESS(f"  X-API-Key:  {app.api_key}"))
        self.stdout.write(self.style.SUCCESS(f"  API Secret: {app.api_secret}"))
        self.stdout.write(self.style.SUCCESS("--------------------------------------------------"))

        # 4. Crear Credenciales SUNAT (BETA)
        cred, cred_created = SunatCredential.objects.get_or_create(
            company=company,
            defaults={
                "sunat_user": "1076337562MODDATOS",
                "sunat_password_encrypted": "MODDATOS",
                "environment": SunatCredential.Environment.BETA
            }
        )
        if cred_created:
            self.stdout.write(self.style.SUCCESS(f"Created SUNAT Credentials for company {ruc} (Environment: BETA)"))
        else:
            self.stdout.write(self.style.WARNING(f"SUNAT Credentials for company {ruc} already exists"))

        self.stdout.write(self.style.SUCCESS("=== SEEDING COMPLETED SUCCESSFULLY ==="))
