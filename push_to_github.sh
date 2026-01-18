#!/bin/bash
# GitHub'a push etmek için script

echo "🚀 ACE Core projesini GitHub'a push ediliyor..."

# Git repository initialize et (eğer yoksa)
if [ ! -d ".git" ]; then
    echo "📦 Git repository initialize ediliyor..."
    git init
fi

# Remote repository kontrolü
if ! git remote | grep -q "^origin$"; then
    echo "🔗 Remote repository ekleniyor..."
    git remote add origin https://github.com/ahmetererr/ace_lib.git
else
    echo "✅ Remote repository zaten var"
fi

# Tüm dosyaları ekle
echo "📝 Dosyalar ekleniyor..."
git add .

# Commit yap
echo "💾 Commit yapılıyor..."
git commit -m "Initial commit: ACE Core framework - Preventing Context Collapse in LLM Agents"

# Main branch oluştur
git branch -M main

# Push et
echo "⬆️  GitHub'a push ediliyor..."
git push -u origin main

echo "✅ Tamamlandı! Proje GitHub'da: https://github.com/ahmetererr/ace_lib"
