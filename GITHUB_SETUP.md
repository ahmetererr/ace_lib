# GitHub Setup Instructions

Bu dosya projeyi GitHub'a push etmek ve başka projelerden import etmek için gerekli adımları içerir.

## 1. GitHub Repository Oluşturma

1. GitHub'da https://github.com/new adresine git
2. Repository adı: `ace_lib` (veya istediğin bir isim)
3. Owner: `ahmetererr`
4. Public veya Private seç
5. README, .gitignore, license EKLEME (zaten var)
6. "Create repository" tıkla

## 2. Projeyi Git Repository Yapma ve Push Etme

```bash
cd /Users/ahmet/capstone

# Git repository initialize et
git init

# Remote repository ekle (GitHub'dan aldığın URL'i kullan)
git remote add origin https://github.com/ahmetererr/ace_lib.git

# Tüm dosyaları ekle
git add .

# İlk commit
git commit -m "Initial commit: ACE Core framework"

# Main branch'e push et
git branch -M main
git push -u origin main
```

## 3. Başka Projelerden Import Etme

### Yöntem 1: pip ile GitHub'dan Install (Önerilen)

```bash
# Başka bir projede
pip install git+https://github.com/ahmetererr/ace_lib.git
```

Sonra kodunda:
```python
from ace_core import ACEFramework, ItemType

ace = ACEFramework()
# ...
```

### Yöntem 2: Development Mode Install

```bash
# Projeyi klonla
git clone https://github.com/ahmetererr/ace_lib.git
cd ace_lib

# Development mode install et (kod değişikliklerinde otomatik güncellenir)
pip install -e .
```

### Yöntem 3: Local Path ile Install

```bash
# Başka bir projede
pip install -e /Users/ahmet/capstone
```

Sonra:
```python
from ace_core import ACEFramework, ItemType
```

## 4. Güncellemeleri Push Etme

```bash
cd /Users/ahmet/capstone

# Değişiklikleri ekle
git add .

# Commit yap
git commit -m "Update: description of changes"

# Push et
git push origin main
```

## 5. Başka Projelerde Güncelleme Alma

```bash
# Eğer pip ile kurduysan
pip install --upgrade git+https://github.com/ahmetererr/ace_lib.git

# Eğer development mode'da kurduysan
cd ace_lib
git pull origin main
```

## Notlar

- GitHub repository public ise herkes kullanabilir
- Private ise GitHub token veya SSH key gerekir
- `setup.py` dosyası sayesinde `pip install` ile kurulabilir
- Version güncellemeleri için `setup.py`'deki `version` değerini değiştir
