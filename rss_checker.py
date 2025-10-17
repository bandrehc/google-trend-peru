import xml.etree.ElementTree as ET
import requests
import hashlib
import os
from datetime import datetime
import pytz

def obtener_rss(url):
    respuesta = requests.get(url)
    respuesta.raise_for_status()
    return respuesta.content

def parsear_rss(contenido_xml):
    raiz = ET.fromstring(contenido_xml)
    elementos = []

    espacios_nombres = {
        'ht': 'https://trends.google.com/trending/rss'
    }

    lima_tz = pytz.timezone('America/Lima')
    
    for elemento in raiz.findall('./channel/item'):
        titulo = elemento.find('title').text
        trafico_aprox = elemento.find('ht:approx_traffic', espacios_nombres).text if elemento.find('ht:approx_traffic', espacios_nombres) else 'N/A'
        fecha_pub = elemento.find('pubDate').text
        
        noticias = []
        for noticia in elemento.findall('ht:news_item', espacios_nombres):
            titulo_noticia = noticia.find('ht:news_item_title', espacios_nombres).text
            url_noticia = noticia.find('ht:news_item_url', espacios_nombres).text
            noticias.append(f"- **{titulo_noticia}**: [Link]({url_noticia})")
        
        noticias_combinadas = "\n".join(noticias)
        
        hash_elemento = hashlib.md5((titulo + fecha_pub).encode()).hexdigest()
        
        elementos.append({
            'Titulo': titulo,
            'Trafico': trafico_aprox,
            'Fecha': fecha_pub,
            'Noticias': noticias_combinadas,
            'Hash': hash_elemento,
            'FechaLima': datetime.now(lima_tz).strftime('%d/%m/%Y %H:%M')
        })
    
    return elementos

def limpiar_archivo_viejo(archivo_markdown, max_entradas=150):
    if not os.path.exists(archivo_markdown):
        return
    
    with open(archivo_markdown, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    secciones = contenido.split('### ')
    if len(secciones) > max_entradas:
        secciones = secciones[:max_entradas]
        contenido_limpio = '### '.join(secciones)
        with open(archivo_markdown, 'w', encoding='utf-8') as f:
            f.write(contenido_limpio)

def actualizar_markdown(elementos_nuevos, archivo_markdown, archivo_procesados):
    if not os.path.exists(archivo_markdown):
        with open(archivo_markdown, 'w', encoding='utf-8') as md:
            md.write("# Tendencias Google Perú 🇵🇪\n\n")

    if os.path.exists(archivo_procesados):
        with open(archivo_procesados, 'r', encoding='utf-8') as f:
            hashes_procesados = set(f.read().splitlines())
    else:
        hashes_procesados = set()

    with open(archivo_markdown, 'r+', encoding='utf-8') as md:
        contenido = md.read()
        md.seek(0, 0)

        entradas_nuevas = []
        for elemento in elementos_nuevos:
            if elemento['Hash'] not in hashes_procesados:
                entrada = f"### {elemento['Titulo']} ({elemento['Trafico']}, {elemento['FechaLima']} Lima)\n\n"
                if elemento['Noticias']:
                    entrada += f"{elemento['Noticias']}\n\n"
                else:
                    entrada += "Sin noticias relacionadas disponibles.\n\n"
                entradas_nuevas.append(entrada)
                hashes_procesados.add(elemento['Hash'])

        if entradas_nuevas:
            md.write("\n".join(entradas_nuevas) + "\n" + contenido)

    with open(archivo_procesados, 'w', encoding='utf-8') as f:
        f.write("\n".join(hashes_procesados))
    
    limpiar_archivo_viejo(archivo_markdown)

url_rss = 'https://trends.google.com/trending/rss?geo=PE'
archivo_markdown = 'trending_news.md'
archivo_procesados = 'processed_hashes.txt'

contenido_rss = obtener_rss(url_rss)
elementos_nuevos = parsear_rss(contenido_rss)
actualizar_markdown(elementos_nuevos, archivo_markdown, archivo_procesados)
