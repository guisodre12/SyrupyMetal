
import unittest
import os
import database as db


class TestEstoque(unittest.TestCase):

    def setUp(self):

        self.banco_teste = "banco_teste.db"

        if os.path.exists(self.banco_teste):
            os.remove(self.banco_teste)

        db.criar_tabelas(self.banco_teste)

        # Cadastrar fornecedor para os testes

        db.cadastro_fornecedor(
            "Fornecedor Teste",
            "11999999999",
            "Fornecedor utilizado nos testes",
            self.banco_teste
        )

        # Cadastrar material inicial

        db.cadastro_material(
            "PST001",
            "Pastilha de metal duro",
            "Fabricante Teste",
            1,
            "Unidade",
            20,
            5,
            self.banco_teste
        )

    def tearDown(self):

        if os.path.exists(self.banco_teste):
            os.remove(self.banco_teste)

    # T01 - CADASTRAR MATERIAL VÁLIDO

    def test_cadastrar_material(self):

        materiais = db.getMateriais(self.banco_teste)

        self.assertEqual(len(materiais), 1)

        self.assertEqual(
            materiais[0][1],
            "PST001"
        )

        print("T01 - Cadastro de material: OK")

    # T02 - BLOQUEAR CÓDIGO DUPLICADO

    def test_codigo_duplicado(self):

        with self.assertRaises(ValueError):

            db.cadastro_material(
                "PST001",
                "Outra pastilha",
                "Fabricante Teste",
                1,
                "Unidade",
                10,
                5,
                self.banco_teste
            )

        materiais = db.getMateriais(self.banco_teste)

        self.assertEqual(len(materiais), 1)

        print("T02 - Bloqueio de código duplicado: OK")

    # T03 - REGISTRAR ENTRADA DE 10 UNIDADES

    def test_entrada_material(self):

        db.registrar_movimentacao(
            1,
            "Entrada",
            10,
            "Recebimento de compra",
            self.banco_teste
        )

        materiais = db.getMateriais(self.banco_teste)

        self.assertEqual(
            materiais[0][6],
            30
        )

        print("T03 - Entrada de materiais: OK")

    # T04 - BLOQUEAR SAÍDA MAIOR QUE O SALDO

    def test_saida_maior_que_saldo(self):

        with self.assertRaises(ValueError):

            db.registrar_movimentacao(
                1,
                "Saída",
                30,
                "Tentativa de retirada",
                self.banco_teste
            )

        materiais = db.getMateriais(self.banco_teste)

        self.assertEqual(
            materiais[0][6],
            20
        )

        print("T04 - Bloqueio de saída sem estoque: OK")

    # T05 - ALERTA DE ESTOQUE MÍNIMO

    def test_estoque_minimo(self):

        db.registrar_movimentacao(
            1,
            "Saída",
            15,
            "Consumo na produção",
            self.banco_teste
        )

        estoque_baixo = db.getEstoqueBaixo(
            self.banco_teste
        )

        self.assertEqual(len(estoque_baixo), 1)

        self.assertEqual(
            estoque_baixo[0][2],
            5
        )

        print("T05 - Alerta de estoque mínimo: OK")

    # TESTE EXTRA - HISTÓRICO

    def test_historico_movimentacao(self):

        movimentacoes = db.getMovimentacoes(
            self.banco_teste
        )

        # O cadastro inicial também gera uma entrada

        self.assertEqual(len(movimentacoes), 1)

        self.assertEqual(
            movimentacoes[0][3],
            "Entrada"
        )

        self.assertEqual(
            movimentacoes[0][4],
            20
        )

        print("Teste extra - Histórico: OK")


if __name__ == "__main__":

    unittest.main(verbosity=2)
