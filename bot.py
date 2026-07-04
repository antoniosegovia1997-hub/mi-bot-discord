def crear_embed(now_utc, nombre_canal):
    # TOMAMOS HORA ESPAÑA Y LA REDONDEAMOS A LA HORA PAR
    hora_actual_es = now_utc.astimezone(TZ_ESPANA)
    
    # Si son las 12:10, la hora del evento es 12:00
    # Si son las 13:10, la hora del evento es 14:00
    hora_evento_es = hora_actual_es.replace(minute=0, second=0, microsecond=0)
    if hora_actual_es.hour % 2!= 0:
        hora_evento_es = hora_evento_es + datetime.timedelta(hours=1)

    # El evento dura 2 horas
    hora_fin_es = hora_evento_es + datetime.timedelta(hours=2)

    # Convertir a UTC y otros países
    hora_inicio_utc = hora_evento_es.astimezone(datetime.timezone.utc)
    hora_fin_utc = hora_fin_es.astimezone(datetime.timezone.utc)
    
    hora_inicio_ve = hora_evento_es.astimezone(TZ_VENEZUELA)
    hora_fin_ve = hora_fin_es.astimezone(TZ_VENEZUELA)

    hora_inicio_co = hora_evento_es.astimezone(TZ_COLOMBIA)
    hora_fin_co = hora_fin_es.astimezone(TZ_COLOMBIA)

    fecha = hora_evento_es.strftime("%d/%m/%y")

    desc = f"**Info del Evento:**\n📅 {fecha}\n\n"
    desc += f"🇪🇸 **ESPAÑA:** {hora_evento_es.strftime('%H:%M')} - {hora_fin_es.strftime('%H:%M')}\n"
    desc += f"🇻🇪 **VENEZUELA:** {hora_inicio_ve.strftime('%H:%M')} - {hora_fin_ve.strftime('%H:%M')}\n"
    desc += f"🇨🇴 **COLOMBIA:** {hora_inicio_co.strftime('%H:%M')} - {hora_fin_co.strftime('%H:%M')}\n\n"
    
    desc += "**Descripción:**\n🔥 VER TIK TOKS NO TE VA A AYUDAR A SUBIR DE NIVEL UNETE!! 🔥\n"

    for i in range(1, 5):
        menciones = []
        for user_id in inscritos[i]:
            user = client.get_user(user_id)
            if user:
                menciones.append(f"<@{user_id}>")
            else:
                menciones.append(f"Usuario {user_id}")

        if not menciones: menciones = ["-"]
        
        canal_voz = i + 1
        desc += f"\n**{NOMBRES_TEAM[i]} ({nombre_canal}) - (ch{canal_voz}) ({len(inscritos[i])}/6)**\n" + "\n".join(menciones) + "\n"

    total = sum(len(v) for v in inscritos.values())
    desc += f"\n**Total Inscritos: {total}/24**"

    embed = discord.Embed(title=f"LOL {nombre_canal}", description=desc, color=0xff0000)
    return embed
