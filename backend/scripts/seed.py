from app.db.session import SessionLocal
from app.models.user import Organization, User
from app.models.rbac import Role, Permission, user_roles
from app.core.security import hash_password


PERMS = [
    "document:create",
    "document:read",
    "document:update",
    "document:delete",
    "document:share",
]


ROLE_PERMS = {
    "admin": PERMS,
    "editor": PERMS[:3],
    "viewer": ["document:read"],
}


def seed():
    db = SessionLocal()

    try:
        # ============================================================
        # Organization
        # ============================================================

        organization = (
            db.query(Organization)
            .filter_by(name="SecureFlow Demo Organization")
            .first()
        )

        if not organization:
            organization = Organization(
                name="SecureFlow Demo Organization"
            )

            db.add(organization)
            db.flush()

        # ============================================================
        # Permissions
        # ============================================================

        permissions = {}

        for permission_code in PERMS:
            permission = (
                db.query(Permission)
                .filter_by(code=permission_code)
                .first()
            )

            if not permission:
                permission = Permission(
                    code=permission_code
                )

                db.add(permission)
                db.flush()

            permissions[permission_code] = permission

        # ============================================================
        # Roles
        # ============================================================

        roles = {}

        for role_name in ["admin", "editor", "viewer"]:
            role = (
                db.query(Role)
                .filter_by(name=role_name)
                .first()
            )

            if not role:
                role = Role(
                    name=role_name
                )

                db.add(role)
                db.flush()

            roles[role_name] = role

        # ============================================================
        # Assign permissions to roles
        # ============================================================

        for role_name, permission_codes in ROLE_PERMS.items():
            role = roles[role_name]

            for permission_code in permission_codes:
                permission = permissions[permission_code]

                if permission not in role.permissions:
                    role.permissions.append(permission)

        # ============================================================
        # Admin user
        # ============================================================

        admin_email = "admin@secureflow.example.com"
        admin_password = "Admin@12345"

        admin = (
            db.query(User)
            .filter_by(email=admin_email)
            .first()
        )

        if not admin:
            admin = User(
                organization_id=organization.id,
                email=admin_email,
                hashed_password=hash_password(admin_password),
                is_active=True,
            )

            db.add(admin)
            db.flush()

        # ============================================================
        # Assign admin role
        # ============================================================

        existing_assignment = db.execute(
            user_roles.select().where(
                user_roles.c.user_id == admin.id,
                user_roles.c.role_id == roles["admin"].id,
            )
        ).first()

        if not existing_assignment:
            db.execute(
                user_roles.insert().values(
                    user_id=admin.id,
                    role_id=roles["admin"].id,
                )
            )

        # ============================================================
        # Commit
        # ============================================================

        db.commit()

        print("Seed completed successfully")
        print(f"Organization: {organization.name}")
        print("Roles: admin, editor, viewer")
        print(
            "Permissions: "
            "document:create, "
            "document:read, "
            "document:update, "
            "document:delete, "
            "document:share"
        )
        print(f"Admin user: {admin_email}")
        print(f"Admin password: {admin_password}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()