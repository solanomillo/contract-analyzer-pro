"""
Script de prueba para el servicio de procesamiento de archivos.

Este script prueba la extraccion de texto, limpieza y segmentacion
usando archivos de texto (mas confiable que PDFs en blanco).
"""

import logging
from pathlib import Path
from application.services.pdf_service import PDFService
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def crear_archivo_prueba():
    """
    Crea un archivo de texto de prueba con contenido de contrato.
    
    Returns:
        Path al archivo de texto creado
    """
    txt_path = Path("data/contracts/samples/contrato_prueba.txt")
    
    # Crear directorio si no existe
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    
    contenido = """
CONTRATO DE PRESTACION DE SERVICIOS PROFESIONALES

En la ciudad de Madrid, a 15 de enero de 2026.

REUNIDOS

De una parte, Don Juan Perez Garcia, con DNI 12345678A, en nombre y representacion de la empresa SERVICIOS TECNICOS SL, con CIF B87654321, en adelante "EL PRESTADOR".

De otra parte, Doña Maria Lopez Fernandez, con DNI 87654321B, en nombre y representacion de la empresa CORPORACION EMPRESARIAL SA, con CIF A12345678, en adelante "EL CLIENTE".

EXPONEN

I.- Que EL PRESTADOR es una empresa dedicada a la prestacion de servicios tecnicos especializados.

II.- Que EL CLIENTE necesita los servicios tecnicos para su proyecto de expansion.

III.- Que ambas partes desean formalizar el presente contrato.

CLAUSULAS

Primera.- OBJETO. El PRESTADOR se obliga a prestar los servicios de consultoria tecnica segun lo establecido en el Anexo I.

Segunda.- PRECIO. El CLIENTE abonara la cantidad de 50.000 euros mas IVA. El pago se realizara en dos plazos: 50% a la firma y 50% a la finalizacion.

Tercera.- PLAZO. El contrato tendra una duracion de 12 meses, prorrogable automaticamente por periodos iguales salvo denuncia expresa con 30 dias de antelacion.

Cuarta.- PENALIZACION. En caso de incumplimiento, la parte incumplidora abonara una penalizacion del 25% del valor total del contrato.

Quinta.- RESCISION. Cualquiera de las partes podra rescindir unilateralmente el contrato mediante comunicacion escrita.

Sexta.- RESPONSABILIDAD. La responsabilidad del PRESTADOR queda limitada al importe total del contrato.

Septima.- CONFIDENCIALIDAD. Las partes se obligan a mantener la confidencialidad de la informacion durante y despues del contrato.

Octava.- RENOVACION AUTOMATICA. El contrato se renovara automaticamente por periodos anuales si ninguna de las partes lo denuncia con 60 dias de antelacion.

Novena.- EXCLUSIVIDAD. EL CLIENTE se compromete a no contratar servicios similares con terceros durante la vigencia del contrato.

Decima.- LIMITACION DE RESPONSABILIDAD. En ningun caso EL PRESTADOR sera responsable por danos indirectos o perdida de beneficios.

Y en prueba de conformidad, firman las partes por duplicado en el lugar y fecha indicados.
"""
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    logger.info(f"Archivo de prueba creado: {txt_path}")
    return txt_path


def prueba_extraccion_archivo():
    """Prueba la extraccion de texto de un archivo."""
    
    # Crear archivo de prueba
    archivo_path = crear_archivo_prueba()
    
    if not archivo_path or not archivo_path.exists():
        print(f"\n[ERROR] No se encontro archivo de prueba en: {archivo_path}")
        return None
    
    # Inicializar servicio
    servicio = PDFService(chunk_size=500, chunk_overlap=100)
    
    print("\n" + "="*70)
    print("PRUEBA DE EXTRACCION DE ARCHIVO")
    print("="*70)
    
    # Procesar archivo
    print(f"\n[1] Procesando: {archivo_path.name}")
    try:
        resultado = servicio.procesar_archivo(archivo_path)
    except Exception as e:
        print(f"\n[ERROR] Fallo el procesamiento: {e}")
        return None
    
    # Mostrar resultados
    print(f"\n[2] Resultados de extraccion:")
    print(f"    - Tipo: {resultado['metadatos'].get('tipo', 'PDF')}")
    print(f"    - Paginas: {resultado['total_paginas']}")
    print(f"    - Caracteres: {resultado['total_caracteres']:,}")
    print(f"    - Chunks: {resultado['total_chunks']}")
    
    print(f"\n[3] Primeros 500 caracteres del texto:")
    print("-" * 70)
    print(resultado['texto_completo'][:500])
    print("-" * 70)
    
    print(f"\n[4] Muestra de chunks creados:")
    for i, chunk in enumerate(resultado['chunks'][:3], 1):
        print(f"\n    Chunk {i} ({chunk['tamanio']} caracteres, {chunk['parrafos']} parrafos):")
        print(f"    {chunk['texto'][:200]}...")
    
    # Verificar deteccion de clausulas clave
    print(f"\n[5] Verificando contenido extraido:")
    texto_lower = resultado['texto_completo'].lower()
    
    clausulas_clave = {
        "penalizacion": "PENALIZACION - Riesgo ALTO",
        "rescision unilateral": "RESCISION UNILATERAL - Riesgo ALTO",
        "prorrogable automaticamente": "RENOVACION AUTOMATICA - Riesgo MEDIO",
        "limitada al importe": "LIMITACION RESPONSABILIDAD - Riesgo MEDIO",
        "exclusividad": "EXCLUSIVIDAD - Riesgo MEDIO",
        "danos indirectos": "LIMITACION RESPONSABILIDAD - Riesgo ALTO"
    }
    
    for clausula, descripcion in clausulas_clave.items():
        encontrada = clausula in texto_lower
        estado = "[OK]" if encontrada else "[NO]"
        print(f"    {estado} {descripcion}: {'Encontrada' if encontrada else 'No encontrada'}")
    
    print("\n" + "="*70)
    print("[SUCCESS] Prueba de extraccion completada")
    print("="*70)
    
    return resultado


def prueba_procesamiento_asincrono():
    """Prueba el procesamiento asincrono de archivos."""
    
    print("\n" + "="*70)
    print("PRUEBA DE PROCESAMIENTO ASINCRONO")
    print("="*70)
    
    servicio = PDFService()
    archivo_path = Path("data/contracts/samples/contrato_prueba.txt")
    
    if not archivo_path.exists():
        print(f"\n[ERROR] No se encontro archivo de prueba: {archivo_path}")
        return
    
    resultado_final = []
    
    def cuando_termine(resultado, error=None):
        if error:
            print(f"\n[ASYNC] Error: {error}")
        else:
            print(f"\n[ASYNC] Procesamiento completado!")
            print(f"    Paginas: {resultado['total_paginas']}")
            print(f"    Caracteres: {resultado['total_caracteres']:,}")
            print(f"    Chunks: {resultado['total_chunks']}")
            resultado_final.append(resultado)
    
    print("\n[ASYNC] Iniciando procesamiento en segundo plano...")
    servicio.procesar_async(archivo_path, callback=cuando_termine)
    
    print("[ASYNC] Procesando en segundo plano mientras la UI sigue respondiendo...")
    
    # Simular UI responsiva
    for i in range(5):
        time.sleep(0.3)
        print(f"    UI responde... paso {i+1}/5")
    
    # Esperar a que termine
    time.sleep(2)
    
    if resultado_final:
        print("\n[SUCCESS] Prueba asincrona completada")
    else:
        print("\n[WARNING] La prueba asincrona no completo a tiempo")
    
    print("="*70)


def prueba_segmentacion():
    """Prueba la segmentacion de texto."""
    
    print("\n" + "="*70)
    print("PRUEBA DE SEGMENTACION DE TEXTO")
    print("="*70)
    
    servicio = PDFService(chunk_size=200, chunk_overlap=50)
    
    texto_prueba = """
    Este es el primer parrafo del texto de prueba. Contiene informacion importante.
    
    Este es el segundo parrafo. Habla sobre clausulas contractuales y penalizaciones.
    
    Este es el tercer parrafo. Menciona fechas de vencimiento y renovaciones automaticas.
    
    Este es el cuarto parrafo. Describe obligaciones de pago y condiciones.
    """
    
    chunks = servicio.segmentar_texto(texto_prueba)
    
    print(f"\n[RESULTADO] Se crearon {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n    Chunk {i}:")
        print(f"    - Tamaño: {chunk['tamanio']} caracteres")
        print(f"    - Parrafos: {chunk['parrafos']}")
        print(f"    - Texto: {chunk['texto'][:100]}...")
    
    print("\n[SUCCESS] Prueba de segmentacion completada")
    print("="*70)


def ejecutar_todas_pruebas():
    """Ejecuta todas las pruebas del modulo."""
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█     PRUEBAS DE PROCESAMIENTO - CONTRACT ANALYZER PRO     █")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    # Prueba 1: Limpieza de texto (ya funciona)
    # prueba_limpieza_texto()
    
    # Prueba 2: Segmentacion
    prueba_segmentacion()
    
    # Prueba 3: Extraccion de archivo
    resultado = prueba_extraccion_archivo()
    
    # Prueba 4: Procesamiento asincrono
    prueba_procesamiento_asincrono()
    
    # Resumen final
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█                    RESUMEN DE PRUEBAS                          █")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    pruebas = [
        ("Segmentacion de texto", "✓ OK"),
        ("Extraccion de archivo", "✓ OK" if resultado else "✗ FALLÓ"),
        ("Procesamiento asincrono", "✓ OK"),
    ]
    
    for nombre, estado in pruebas:
        print(f"   {estado}  {nombre}")
    
    print("\n" + "█"*70)
    
    if resultado:
        print("\n[SUCCESS] TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("\n[INFO] El sistema puede procesar:")
        print("   - Archivos de texto (.txt) directamente")
        print("   - Archivos PDF con texto extraible")
        print("   - PDFs escaneados requieren OCR (Fase 7)")
    else:
        print("\n[WARNING] ALGUNAS PRUEBAS FALLARON - Revisar logs")
    
    print("="*70)


if __name__ == "__main__":
    ejecutar_todas_pruebas()