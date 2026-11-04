
import streamlit as st
import pandas as pd
import database as db
from datetime import date


# CONFIGURAÇÕES

st.set_page_config(
    page_title="DDA Metalúrgica",
    page_icon="🏭",
    layout="wide"
)

db.criar_tabelas()

st.title("🏭 DDA METALÚRGICA")
st.caption("Sistema de Controle de Estoque de Pastilhas Industriais")

st.sidebar.title("Menu Principal")

menu = st.sidebar.selectbox(
    "Selecione uma opção",
    [
        "Painel Inicial",
        "Cadastrar Material",
        "Consultar Materiais",
        "Cadastrar Fornecedor",
        "Movimentação",
        "Histórico",
        "Relatórios"
    ]
)


# PAINEL INICIAL

if menu == "Painel Inicial":

    st.header("Painel de Controle")

    total, criticos, movimentacoes = db.getIndicadores()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total de materiais", total)
    col2.metric("Estoque crítico", criticos)
    col3.metric("Movimentações", movimentacoes)

    st.divider()

    st.subheader("⚠️ Materiais com estoque crítico")

    estoque_baixo = db.getEstoqueBaixo()

    if estoque_baixo:

        df = pd.DataFrame(
            estoque_baixo,
            columns=[
                "Código",
                "Descrição",
                "Saldo Atual",
                "Estoque Mínimo"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.warning("Existem materiais que precisam de atenção.")

    else:
        st.success("Nenhum material está com estoque crítico.")

    st.divider()

    st.subheader("Movimentações recentes")

    movimentacoes_recentes = db.getMovimentacoes()[:5]

    if movimentacoes_recentes:

        df = pd.DataFrame(
            movimentacoes_recentes,
            columns=[
                "ID",
                "Código",
                "Material",
                "Tipo",
                "Quantidade",
                "Data e Hora",
                "Observação"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Nenhuma movimentação registrada.")


# CADASTRAR MATERIAL

elif menu == "Cadastrar Material":

    st.header("Cadastro de Materiais")

    fornecedores = db.getFornecedores()

    if not fornecedores:

        st.warning("Cadastre um fornecedor antes de cadastrar materiais.")

    else:

        with st.form("form_material"):

            codigo = st.text_input("Código do material")

            descricao = st.text_input("Descrição da pastilha")

            fabricante = st.text_input("Fabricante")

            fornecedor = st.selectbox(
                "Fornecedor",
                fornecedores,
                format_func=lambda f: f[1]
            )

            unidade = st.selectbox(
                "Unidade de medida",
                [
                    "Unidade",
                    "Peça",
                    "Caixa",
                    "Kg",
                    "Metro"
                ]
            )

            col1, col2 = st.columns(2)

            with col1:
                saldo = st.number_input(
                    "Quantidade inicial",
                    min_value=0,
                    step=1
                )

            with col2:
                minimo = st.number_input(
                    "Estoque mínimo",
                    min_value=0,
                    step=1
                )

            cadastrar = st.form_submit_button(
                "Cadastrar Material",
                use_container_width=True
            )

            if cadastrar:

                try:

                    resultado = db.cadastro_material(
                        codigo,
                        descricao,
                        fabricante,
                        fornecedor[0],
                        unidade,
                        saldo,
                        minimo
                    )

                    st.success(resultado)

                except ValueError as erro:

                    st.error(str(erro))

                except Exception as erro:

                    st.error(f"Erro ao cadastrar: {erro}")


# CONSULTAR MATERIAIS

elif menu == "Consultar Materiais":

    st.header("Consulta de Materiais")

    pesquisa = st.text_input(
        "Pesquisar por código ou descrição",
        placeholder="Digite o código ou nome da pastilha"
    )

    if pesquisa:

        materiais = db.pesquisar_material(pesquisa)

    else:

        materiais = db.getMateriais()

    if materiais:

        df = pd.DataFrame(
            materiais,
            columns=[
                "ID",
                "Código",
                "Descrição",
                "Fabricante",
                "Fornecedor",
                "Unidade",
                "Saldo Atual",
                "Estoque Mínimo"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Situação do estoque")

        for material in materiais:

            codigo = material[1]
            descricao = material[2]
            saldo = material[6]
            minimo = material[7]

            if saldo <= minimo:

                st.error(
                    f"⚠️ {codigo} - {descricao}: "
                    f"Estoque crítico! Saldo: {saldo}"
                )

            else:

                st.success(
                    f"✅ {codigo} - {descricao}: "
                    f"Estoque normal. Saldo: {saldo}"
                )

    else:

        st.info("Nenhum material encontrado.")


# CADASTRAR FORNECEDOR

elif menu == "Cadastrar Fornecedor":

    st.header("Cadastro de Fornecedores")

    with st.form("form_fornecedor"):

        nome = st.text_input("Nome do fornecedor")

        contato = st.text_input("Contato")

        observacoes = st.text_area("Observações")

        cadastrar = st.form_submit_button(
            "Cadastrar Fornecedor"
        )

        if cadastrar:

            try:

                resultado = db.cadastro_fornecedor(
                    nome,
                    contato,
                    observacoes
                )

                st.success(resultado)

            except ValueError as erro:

                st.error(str(erro))

            except Exception as erro:

                st.error(f"Erro: {erro}")

    st.divider()

    st.subheader("Fornecedores cadastrados")

    fornecedores = db.getFornecedores()

    if fornecedores:

        df = pd.DataFrame(
            fornecedores,
            columns=[
                "ID",
                "Nome",
                "Contato",
                "Observações"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("Nenhum fornecedor cadastrado.")


# MOVIMENTAÇÃO

elif menu == "Movimentação":

    st.header("Movimentação de Estoque")

    materiais = db.getMateriais()

    if not materiais:

        st.warning("Cadastre um material antes de realizar movimentações.")

    else:

        with st.form("form_movimentacao"):

            material = st.selectbox(
                "Selecione o material",
                materiais,
                format_func=lambda m:
                f"{m[1]} - {m[2]} | Saldo: {m[6]} {m[5]}"
            )

            st.write(
                f"**Saldo disponível:** {material[6]} {material[5]}"
            )

            tipo = st.selectbox(
                "Tipo de movimentação",
                ["Entrada", "Saída"]
            )

            quantidade = st.number_input(
                "Quantidade",
                min_value=1,
                step=1
            )

            observacao = st.text_area(
                "Observação"
            )

            registrar = st.form_submit_button(
                "Confirmar movimentação",
                use_container_width=True
            )

            if registrar:

                try:

                    resultado = db.registrar_movimentacao(
                        material[0],
                        tipo,
                        quantidade,
                        observacao
                    )

                    st.success(resultado)

                    st.info(
                        f"Novo saldo: "
                        f"{material[6] + quantidade if tipo == 'Entrada' else material[6] - quantidade} "
                        f"{material[5]}"
                    )

                except ValueError as erro:

                    st.error(str(erro))

                except Exception as erro:

                    st.error(f"Erro na movimentação: {erro}")


# HISTÓRICO

elif menu == "Histórico":

    st.header("Histórico de Movimentações")

    movimentacoes = db.getMovimentacoes()

    if movimentacoes:

        df = pd.DataFrame(
            movimentacoes,
            columns=[
                "ID",
                "Código",
                "Material",
                "Tipo",
                "Quantidade",
                "Data e Hora",
                "Observação"
            ]
        )

        df["Data e Hora"] = pd.to_datetime(
            df["Data e Hora"]
        )

        st.subheader("Filtrar por período")

        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input(
                "Data inicial",
                value=date.today().replace(day=1)
            )

        with col2:
            data_fim = st.date_input(
                "Data final",
                value=date.today()
            )

        if data_inicio > data_fim:

            st.error("A data inicial não pode ser maior que a data final.")

        else:

            filtrado = df[
                (df["Data e Hora"].dt.date >= data_inicio) &
                (df["Data e Hora"].dt.date <= data_fim)
            ]

            st.dataframe(
                filtrado,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "Baixar histórico em CSV",
                data=filtrado.to_csv(
                    index=False
                ).encode("utf-8-sig"),
                file_name="historico_movimentacoes.csv",
                mime="text/csv"
            )

    else:

        st.info("Ainda não existem movimentações registradas.")


# RELATÓRIOS

elif menu == "Relatórios":

    st.header("Relatórios de Estoque")

    materiais = db.getMateriais()

    if materiais:

        df = pd.DataFrame(
            materiais,
            columns=[
                "ID",
                "Código",
                "Descrição",
                "Fabricante",
                "Fornecedor",
                "Unidade",
                "Saldo Atual",
                "Estoque Mínimo"
            ]
        )

        total_itens = df["Saldo Atual"].sum()

        total_criticos = len(
            df[df["Saldo Atual"] <= df["Estoque Mínimo"]]
        )

        col1, col2 = st.columns(2)

        col1.metric("Quantidade total em estoque", int(total_itens))

        col2.metric("Materiais críticos", total_criticos)

        st.subheader("Saldo por material")

        st.bar_chart(
            df.set_index("Código")["Saldo Atual"]
        )

        st.subheader("Resumo de movimentações")

        resumo = db.getResumoMovimentacoes()

        if resumo:

            df_resumo = pd.DataFrame(
                resumo,
                columns=["Tipo", "Quantidade"]
            )

            st.dataframe(
                df_resumo,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("Não existem movimentações para apresentar.")

        st.download_button(
            "Baixar relatório de estoque",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="relatorio_estoque.csv",
            mime="text/csv"
        )

    else:

        st.info("Cadastre materiais para gerar relatórios.")
