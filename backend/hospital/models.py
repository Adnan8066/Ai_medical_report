"""Hospital profile, departments and indoor navigation data."""

from django.db import models


class Hospital(models.Model):
    """Single row describing the fictional demo hospital."""

    name = models.CharField(max_length=160)
    code = models.CharField(max_length=20, default="ASTERNOVA")
    hospital_type = models.CharField(max_length=80, default="Multispeciality Hospital")
    established_year = models.PositiveIntegerField(default=2012)
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    postal_code = models.CharField(max_length=12, blank=True)
    country = models.CharField(max_length=80, default="India")
    phone = models.CharField(max_length=30, blank=True)
    emergency_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.CharField(max_length=120, blank=True)
    registration_number = models.CharField(max_length=60, blank=True)
    total_beds = models.PositiveIntegerField(default=350)
    icu_beds = models.PositiveIntegerField(default=40)
    emergency_beds = models.PositiveIntegerField(default=20)
    logo = models.ImageField(upload_to="hospital/", null=True, blank=True)
    about = models.TextField(blank=True)
    is_demo = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hospital"
        verbose_name_plural = "Hospital"

    def __str__(self):
        return self.name

    @property
    def full_address(self):
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(part for part in parts if part)


class Department(models.Model):
    """Clinical or support department."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=12, unique=True)
    hod = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="departments_led",
    )
    floor = models.CharField(max_length=40, blank=True)
    location = models.CharField(max_length=120, blank=True)
    contact_extension = models.CharField(max_length=12, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    bed_count = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_clinical = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Floor(models.Model):
    """A physical floor of the hospital used by the navigation module."""

    number = models.IntegerField(unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Floor {self.number} - {self.name}"


class MapLocation(models.Model):
    """
    A searchable point of interest on the indoor map.

    Coordinates are on a simple 1000x700 virtual grid so the frontend can draw
    the floor plan and a route without a mapping provider.
    """

    CATEGORY_CHOICES = [
        ("department", "Department"),
        ("diagnostics", "Diagnostics"),
        ("service", "Patient Service"),
        ("critical", "Critical Care"),
        ("facility", "Facility"),
        ("support", "Support"),
    ]

    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="department")
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="map_locations",
    )
    description = models.CharField(max_length=250, blank=True)
    keywords = models.CharField(
        max_length=250, blank=True, help_text="Extra search terms, comma separated."
    )
    x = models.PositiveIntegerField(default=0)
    y = models.PositiveIntegerField(default=0)
    is_wheelchair_accessible = models.BooleanField(default=True)
    is_landmark = models.BooleanField(default=False)

    class Meta:
        ordering = ["floor__number", "name"]

    def __str__(self):
        return f"{self.name} (Floor {self.floor.number})"
