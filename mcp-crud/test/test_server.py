"""
Tests unitarios para el servidor MCP CRUD.
Ejecutar con: pytest tests/test_server.py -v
"""

import os
import sys
import tempfile
import pytest

# Apuntar la DB a un archivo temporal para tests
tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
tmp.close()
os.environ["DB_PATH"] = tmp.name

# Importar después de setear la variable de entorno
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from server import (
    init_db,
    create_product,
    list_products,
    get_product,
    update_product,
    delete_product,
    search_products,
    get_stats,
)


@pytest.fixture(autouse=True)
def setup_db():
    """Inicializa y limpia la DB antes de cada test."""
    import sqlite3
    init_db()
    with sqlite3.connect(tmp.name) as conn:
        conn.execute("DELETE FROM products")
        conn.commit()
    yield


# ── CREATE ─────────────────────────────────────────────────────────────────────

def test_create_product_basic():
    p = create_product(name="Laptop", price=1299.99, category="electronics", stock=10)
    assert p["id"] is not None
    assert p["name"] == "Laptop"
    assert p["price"] == 1299.99
    assert p["category"] == "electronics"
    assert p["stock"] == 10


def test_create_product_defaults():
    p = create_product(name="Widget", price=9.99)
    assert p["category"] == "general"
    assert p["stock"] == 0


def test_create_product_invalid_price():
    with pytest.raises(ValueError, match="precio"):
        create_product(name="Bad", price=-1)


def test_create_product_empty_name():
    with pytest.raises(ValueError, match="nombre"):
        create_product(name="  ", price=10)


# ── READ ───────────────────────────────────────────────────────────────────────

def test_get_product_found():
    created = create_product(name="Mouse", price=29.99)
    fetched = get_product(created["id"])
    assert fetched["name"] == "Mouse"


def test_get_product_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        get_product(99999)


def test_list_products_empty():
    result = list_products()
    assert result["items"] == []
    assert result["total"] == 0


def test_list_products_with_data():
    create_product(name="A", price=10, category="cat1", stock=5)
    create_product(name="B", price=20, category="cat2", stock=0)
    result = list_products()
    assert result["total"] == 2


def test_list_products_filter_category():
    create_product(name="A", price=10, category="tech")
    create_product(name="B", price=20, category="food")
    result = list_products(category="tech")
    assert result["total"] == 1
    assert result["items"][0]["category"] == "tech"


def test_list_products_in_stock_only():
    create_product(name="A", price=10, stock=5)
    create_product(name="B", price=20, stock=0)
    result = list_products(in_stock_only=True)
    assert result["total"] == 1


def test_list_products_price_range():
    create_product(name="Cheap", price=5)
    create_product(name="Mid", price=50)
    create_product(name="Expensive", price=500)
    result = list_products(min_price=10, max_price=100)
    assert result["total"] == 1
    assert result["items"][0]["name"] == "Mid"


# ── UPDATE ─────────────────────────────────────────────────────────────────────

def test_update_product_name():
    p = create_product(name="Old Name", price=10)
    updated = update_product(p["id"], name="New Name")
    assert updated["name"] == "New Name"
    assert updated["price"] == 10  # no cambió


def test_update_product_multiple_fields():
    p = create_product(name="X", price=10, stock=1)
    updated = update_product(p["id"], price=99.99, stock=100)
    assert updated["price"] == 99.99
    assert updated["stock"] == 100


def test_update_product_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        update_product(99999, name="Ghost")


def test_update_product_no_fields():
    p = create_product(name="X", price=10)
    with pytest.raises(ValueError, match="al menos un campo"):
        update_product(p["id"])


# ── DELETE ─────────────────────────────────────────────────────────────────────

def test_delete_product():
    p = create_product(name="Temp", price=1)
    result = delete_product(p["id"])
    assert result["deleted"] is True
    with pytest.raises(ValueError):
        get_product(p["id"])


def test_delete_product_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        delete_product(99999)


# ── SEARCH ─────────────────────────────────────────────────────────────────────

def test_search_products_by_name():
    create_product(name="Gaming Mouse", price=59)
    create_product(name="Gaming Keyboard", price=89)
    create_product(name="Desk Lamp", price=29)
    result = search_products("Gaming")
    assert result["total"] == 2


def test_search_products_by_category():
    create_product(name="A", price=10, category="peripherals")
    create_product(name="B", price=20, category="monitors")
    result = search_products("periph")
    assert result["total"] == 1


# ── STATS ──────────────────────────────────────────────────────────────────────

def test_get_stats_empty():
    stats = get_stats()
    assert stats["total_products"] == 0


def test_get_stats_with_data():
    create_product(name="A", price=10, category="tech", stock=5)
    create_product(name="B", price=20, category="tech", stock=10)
    create_product(name="C", price=30, category="food", stock=3)
    stats = get_stats()
    assert stats["total_products"] == 3
    assert stats["average_price"] == 20.0
    assert stats["total_stock"] == 18
    assert len(stats["by_category"]) == 2
