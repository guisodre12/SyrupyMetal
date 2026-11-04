
import sqlite3
from datetime import datetime


def conectar(nome_banco="dda_metalurgica.db"):
    conn = sqlite3.connect(nome_banco)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# CRIAR TABELAS

def criar_tabelas(nome_banco="dda_metalurgica.db"):

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornecedor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            contato TEXT,
            observacoes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            descricao TEXT NOT NULL,
            fabricante TEXT NOT NULL,
            fornecedor_id INTEGER,
            unidade TEXT NOT NULL,
            saldo_atual INTEGER NOT NULL DEFAULT 0,
            estoque_minimo INTEGER NOT NULL,
            FOREIGN KEY (fornecedor_id)
            REFERENCES fornecedor(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            quantidade INTEGER NOT NULL CHECK (quantidade > 0),
            data_hora TEXT NOT NULL,
            observacao TEXT,
            FOREIGN KEY (material_id)
            REFERENCES material(id)
        )
    """)

    conn.commit()
    conn.close()


# CADASTRAR FORNECEDOR

def cadastro_fornecedor(nome, contato, observacoes,
                        nome_banco="dda_metalurgica.db"):

    if not nome.strip():
        raise ValueError("Informe o nome do fornecedor.")

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO fornecedor (nome, contato, observacoes)
            VALUES (?, ?, ?)
        """, (nome, contato, observacoes))

        conn.commit()
        return "Fornecedor cadastrado com sucesso!"

    finally:
        conn.close()


# CONSULTAR FORNECEDORES

def getFornecedores(nome_banco="dda_metalurgica.db"):

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, contato, observacoes
        FROM fornecedor
        ORDER BY nome
    """)

    dados = cursor.fetchall()
    conn.close()

    return dados


# CADASTRAR MATERIAL

def cadastro_material(codigo, descricao, fabricante, fornecedor_id,
                      unidade, saldo_atual, estoque_minimo,
                      nome_banco="dda_metalurgica.db"):

    if not codigo.strip():
        raise ValueError("Informe o código do material.")

    if not descricao.strip():
        raise ValueError("Informe a descrição.")

    if not fabricante.strip():
        raise ValueError("Informe o fabricante.")

    if saldo_atual < 0 or estoque_minimo < 0:
        raise ValueError("Os valores não podem ser negativos.")

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO material (
                codigo, descricao, fabricante, fornecedor_id,
                unidade, saldo_atual, estoque_minimo
            )
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (
            codigo.strip(),
            descricao.strip(),
            fabricante.strip(),
            fornecedor_id,
            unidade,
            estoque_minimo
        ))

        material_id = cursor.lastrowid

        # Registrar estoque inicial no histórico

        if saldo_atual > 0:

            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO movimentacao (
                    material_id, tipo, quantidade,
                    data_hora, observacao
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                material_id,
                "Entrada",
                saldo_atual,
                data_hora,
                "Estoque inicial"
            ))

        cursor.execute("""
            UPDATE material
            SET saldo_atual = ?
            WHERE id = ?
        """, (saldo_atual, material_id))

        conn.commit()

        return "Material cadastrado com sucesso!"

    except sqlite3.IntegrityError as erro:
        conn.rollback()

        if "UNIQUE" in str(erro):
            raise ValueError("Já existe um material com esse código.")

        raise ValueError("Erro ao cadastrar material.")

    finally:
        conn.close()


# CONSULTAR MATERIAIS

def getMateriais(nome_banco="dda_metalurgica.db"):

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            material.id,
            material.codigo,
            material.descricao,
            material.fabricante,
            fornecedor.nome,
            material.unidade,
            material.saldo_atual,
            material.estoque_minimo
        FROM material
        LEFT JOIN fornecedor
        ON material.fornecedor_id = fornecedor.id
        ORDER BY material.codigo
    """)

    dados = cursor.fetchall()
    conn.close()

    return dados


# PESQUISAR MATERIAL

def pesquisar_material(termo, nome_banco="dda_metalurgica.db"):

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            material.id,
            material.codigo,
            material.descricao,
            material.fabricante,
            fornecedor.nome,
            material.unidade,
            material.saldo_atual,
            material.estoque_minimo
        FROM material
        LEFT JOIN fornecedor
        ON material.fornecedor_id = fornecedor.id
        WHERE material.codigo LIKE ?
        OR material.descricao LIKE ?
        ORDER BY material.codigo
    """, (f"%{termo}%", f"%{termo}%"))

    dados = cursor.fetchall()
    conn.close()

    return dados


# REGISTRAR MOVIMENTAÇÃO

def registrar_movimentacao(material_id, tipo, quantidade,
                           observacao="",
                           nome_banco="dda_metalurgica.db"):

    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    if tipo not in ["Entrada", "Saída"]:
        raise ValueError("Tipo de movimentação inválido.")

    conn = conectar(nome_banco)

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT saldo_atual
            FROM material
            WHERE id = ?
        """, (material_id,))

        material = cursor.fetchone()

        if material is None:
            raise ValueError("Material não encontrado.")

        saldo = material[0]

        if tipo == "Saída" and quantidade > saldo:
            raise ValueError("Estoque insuficiente para realizar a saída.")

        if tipo == "Entrada":
            novo_saldo = saldo + quantidade
        else:
            novo_saldo = saldo - quantidade

        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO movimentacao (
                material_id, tipo, quantidade,
                data_hora, observacao
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            material_id,
            tipo,
            quantidade,
            data_hora,
            observacao
        ))

        cursor.execute("""
            UPDATE material
            SET saldo_atual = ?
            WHERE id = ?
        """, (novo_saldo, material_id))

        conn.commit()

        return "Movimentação registrada com sucesso!"

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# CONSULTAR HISTÓRICO

def getMovimentacoes(nome_banco="dda_metalurgica.db"):

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            movimentacao.id,
            material.codigo,
            material.descricao,
            movimentacao.tipo,
            movimentacao.quantidade,
            movimentacao.data_hora,
            movimentacao.observacao
        FROM movimentacao
        INNER JOIN material
        ON movimentacao.material_id = material.id
        ORDER BY movimentacao.id DESC
    """)

    dados = cursor.fetchall()
    conn.close()

    return dados


# CONSULTAR ESTOQUE CRÍTICO

def getEstoqueBaixo(nome_banco="dda_metalurgica.db"):

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT codigo, descricao, saldo_atual, estoque_minimo
        FROM material
        WHERE saldo_atual <= estoque_minimo
        ORDER BY saldo_atual
    """)

    dados = cursor.fetchall()
    conn.close()

    return dados


# INDICADORES DO PAINEL

def getIndicadores(nome_banco="dda_metalurgica.db"):

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM material")
    total_materiais = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM material
        WHERE saldo_atual <= estoque_minimo
    """)
    estoque_critico = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM movimentacao")
    total_movimentacoes = cursor.fetchone()[0]

    conn.close()

    return total_materiais, estoque_critico, total_movimentacoes


# RELATÓRIO DE MOVIMENTAÇÕES

def getResumoMovimentacoes(nome_banco="dda_metalurgica.db"):

    conn = conectar(nome_banco)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tipo, SUM(quantidade)
        FROM movimentacao
        GROUP BY tipo
    """)

    dados = cursor.fetchall()
    conn.close()

    return dados
