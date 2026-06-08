# 🎯 Referencia Rápida - Módulos SUNAT

## Tabla de Contenidos
- [Instalación](#instalación)
- [Uso CLI](#uso-cli)
- [Uso Programático](#uso-programático)
- [Clases Principales](#clases-principales)
- [Ejemplos Comunes](#ejemplos-comunes)

---

## Instalación

```bash
pip install lxml signxml cryptography requests
```

---

## Uso CLI

### Generar Boleta
```bash
python main.py --tipo boleta
```

### Generar y Firmar Boleta
```bash
python main.py --tipo boleta --sign --pfx certificado.pfx --pfx-password "contraseña"
```

### Generar, Firmar y Enviar a SUNAT
```bash
python main.py --tipo boleta --sign --send --pfx cert.pfx --pfx-password "pass" --ambiente beta
```

### Generar Factura
```bash
python main.py --tipo factura --sign --send --pfx cert.pfx --pfx-password "pass"
```

### Ayuda
```bash
python main.py --help
```
