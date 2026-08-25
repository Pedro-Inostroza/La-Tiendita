def roles(request):
    user = request.user
    return {
        "es_administrador": user.is_authenticated and (
            user.is_superuser or user.groups.filter(name="Administrador").exists()
        )
    }
