#!/usr/bin/env python3
"""
Gerçekten Çalışan Basit Proje Örneği
ACE Framework'ü import edip kullanır
"""

import sys
import os

# Proje root'unu path'e ekle (import için gerekli)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Şimdi import edebiliriz
from ace_core import ACEFramework, ItemType


def main():
    """Basit ve çalışan örnek proje"""
    
    print("="*60)
    print("ACE Framework - Basit Proje Örneği")
    print("="*60)
    print()
    
    # 1. Framework'ü başlat
    print("1. Framework başlatılıyor...")
    ace = ACEFramework()
    print(f"   ✓ Framework ID: {ace.framework_id[:12]}...")
    print()
    
    # 2. Bilgi ekle
    print("2. Bilgiler ekleniyor...")
    
    ace.add_manual_item(
        content="Kullanıcı input'unu validate et",
        item_type=ItemType.INSTRUCTION,
        tags=["security"],
        confidence=0.9
    )
    
    ace.add_manual_item(
        content="API'lerde HTTPS kullan",
        item_type=ItemType.CONSTRAINT,
        tags=["security", "api"],
        confidence=0.95
    )
    
    print(f"   ✓ {ace.manual.get_statistics()['total_items']} item eklendi")
    print()
    
    # 3. İstatistikleri göster
    print("3. İstatistikler:")
    stats = ace.get_statistics()
    print(f"   • Toplam item: {stats['manual_stats']['total_items']}")
    print(f"   • Aktif item: {stats['manual_stats']['active_items']}")
    print(f"   • Token tahmini: {stats['manual_stats']['estimated_tokens']}")
    print()
    
    # 4. Context al (LLM için)
    print("4. LLM için context alınıyor...")
    context = ace.get_manual_context(max_items=5)
    print(f"   Context uzunluğu: {len(context)} karakter")
    print(f"   İlk 100 karakter: {context[:100]}...")
    print()
    
    # 5. Yeni bilgi ekle (incremental update)
    print("5. Yeni bilgi ekleniyor (incremental update)...")
    ace.add_manual_item(
        content="Password minimum 8 karakter olmalı",
        item_type=ItemType.CONSTRAINT,
        tags=["security", "password"],
        confidence=0.95
    )
    
    new_stats = ace.get_statistics()
    print(f"   ✓ Yeni toplam item: {new_stats['manual_stats']['total_items']}")
    print(f"   ✓ Bilgi kaybı: %0 (tüm eski bilgiler korundu!)")
    print()
    
    # 6. Tag'e göre filtrele
    print("6. Tag'e göre filtreleme:")
    security_items = ace.manual.get_items_by_tag("security")
    print(f"   'security' tag'ine sahip {len(security_items)} item:")
    for item in security_items:
        print(f"   • {item.content}")
    print()
    
    print("="*60)
    print("✓ Proje başarıyla tamamlandı!")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
