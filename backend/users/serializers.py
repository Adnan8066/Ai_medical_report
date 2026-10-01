from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Role, RoleCode, User
from .roles import MODULE_LABELS


class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Role
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_system",
            "permissions",
            "user_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["code", "is_system", "created_at", "updated_at"]

    def validate_permissions(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Permissions must be a module/action mapping."
            )
        valid_actions = {"view", "create", "edit", "delete", "*"}
        for module, actions in value.items():
            if module not in MODULE_LABELS:
                raise serializers.ValidationError(f"Unknown module '{module}'.")
            if not isinstance(actions, list) or not set(actions) <= valid_actions:
                raise serializers.ValidationError(
                    f"Module '{module}' must list any of {sorted(valid_actions)}."
                )
        return value


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    role_name = serializers.CharField(source="get_role_display", read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "role_name",
            "employee_id",
            "phone",
            "department",
            "department_name",
            "designation",
            "is_active",
            "is_staff",
            "is_demo",
            "last_login",
            "last_seen",
            "date_joined",
        ]
        read_only_fields = ["last_login", "last_seen", "date_joined", "is_demo"]


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "employee_id",
            "phone",
            "department",
            "designation",
            "is_active",
            "password",
        ]

    def validate_role(self, value):
        request = self.context.get("request")
        if value == RoleCode.SUPER_ADMIN and request is not None:
            user = request.user
            if not (user.is_superuser or user.role == RoleCode.SUPER_ADMIN):
                raise serializers.ValidationError(
                    "Only a Super Admin can grant the Super Admin role."
                )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        help_text="Demo email address or username.", trim_whitespace=True
    )
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class MeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    role_name = serializers.CharField(source="get_role_display", read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    permissions = serializers.SerializerMethodField()
    patient_id = serializers.SerializerMethodField()
    doctor_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "first_name",
            "last_name",
            "role",
            "role_name",
            "employee_id",
            "phone",
            "designation",
            "department",
            "department_name",
            "is_demo",
            "permissions",
            "patient_id",
            "doctor_id",
            "last_login",
        ]

    def get_permissions(self, obj):
        return obj.permission_matrix()

    def get_patient_id(self, obj):
        profile = getattr(obj, "patient_profile", None)
        return profile.patient_id if profile else None

    def get_doctor_id(self, obj):
        profile = getattr(obj, "doctor_profile", None)
        return profile.doctor_id if profile else None
