import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import base64
from fpdf import FPDF

# Configuração da página (Com o Ícone de Escudo na aba do navegador)
st.set_page_config(page_title="Compliance | Painel", page_icon="🛡️", layout="wide")

# --- ESTILO PREMIUM (CSS Personalizado) ---
st.markdown("""
    <style>
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s;
            border-left: 5px solid #1f2937; /* Detalhe em cinza escuro/chumbo corporativo */
        }
        
        /* Ajuste do modo escuro para os cartões de métricas */
        @media (prefers-color-scheme: dark) {
            div[data-testid="metric-container"] {
                background-color: #1e293b;
                border-color: #334155;
                border-left: 5px solid #f59e0b; /* Dourado no modo escuro */
            }
        }
        
        div[data-testid="metric-container"]:hover {
            transform: scale(1.02);
            box-shadow: 4px 4px 15px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO PRINCIPAL ---
st.title("⚖️ Sistema Analítico de Compliance")
st.markdown("Monitorização de **Governança, Riscos e Conformidade (GRC)**")
st.divider()

# --- BARRA LATERAL (LOGÓTIPO QUE MUDA COM O TEMA) ---
# Usando Base64 e CSS para alternar a logo nativamente entre Claro/Escuro
if os.path.exists("logo_light.png") and os.path.exists("logo_dark.png"):
    with open("logo_light.png", "rb") as f:
        light_b64 = base64.b64encode(f.read()).decode()
    with open("logo_dark.png", "rb") as f:
        dark_b64 = base64.b64encode(f.read()).decode()
        
    st.sidebar.markdown(f"""
        <style>
            .logo-light {{ display: block; width: 100%; margin-bottom: 15px; }}
            .logo-dark {{ display: none; width: 100%; margin-bottom: 15px; }}
            @media (prefers-color-scheme: dark) {{
                .logo-light {{ display: none; }}
                .logo-dark {{ display: block; }}
            }}
        </style>
        <img src="data:image/png;base64,{light_b64}" class="logo-light">
        <img src="data:image/png;base64,{dark_b64}" class="logo-dark">
    """, unsafe_allow_html=True)
else:
    st.sidebar.info("💡 Guarde 'logo_light.png' e 'logo_dark.png' na pasta do projeto para exibir o logótipo.")

st.sidebar.markdown("### 🛡️ Governança e Risco")
st.sidebar.markdown("Faça o upload da base de dados atualizada para iniciar a análise.")

ficheiro_upload = st.sidebar.file_uploader("Carregar ficheiro (.xlsx)", type=["xlsx"])

# --- LÓGICA PRINCIPAL ---
if ficheiro_upload is not None:
    
    @st.cache_data
    def processar_planilha(ficheiro):
        df = pd.read_excel(ficheiro)
        df.columns = df.columns.str.strip() 
        return df

    df = processar_planilha(ficheiro_upload)
    st.sidebar.divider()
    
    st.sidebar.header("🔍 Filtros Avançados")
    filtro_num = st.sidebar.text_input("Procurar por Número de Processo")
    
    def pegar_unicos(coluna):
        return df[coluna].dropna().unique() if coluna in df.columns else []

    filtro_tipo = st.sidebar.multiselect("Tipo de Documento", pegar_unicos("TIPO DOCUMENTO"))
    filtro_area = st.sidebar.multiselect("Área Requerente", pegar_unicos("Area Demandante"))
    filtro_status = st.sidebar.multiselect("Estado (Status)", pegar_unicos("Status"))
    filtro_risco = st.sidebar.multiselect("Risco do Tema", pegar_unicos("Risco_Tema"))
    filtro_resultado = st.sidebar.multiselect("Resultado", pegar_unicos("Resultado"))

    df_filtrado = df.copy()

    if filtro_num and "Num_Processo" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Num_Processo"].astype(str).str.contains(filtro_num, case=False, na=False)]
    if filtro_tipo:
        df_filtrado = df_filtrado[df_filtrado["TIPO DOCUMENTO"].isin(filtro_tipo)]
    if filtro_area:
        df_filtrado = df_filtrado[df_filtrado["Area Demandante"].isin(filtro_area)]
    if filtro_status:
        df_filtrado = df_filtrado[df_filtrado["Status"].isin(filtro_status)]
    if filtro_risco:
        df_filtrado = df_filtrado[df_filtrado["Risco_Tema"].isin(filtro_risco)]
    if filtro_resultado:
        df_filtrado = df_filtrado[df_filtrado["Resultado"].isin(filtro_resultado)]

    st.markdown("### 📈 Visão Estratégica")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Pareceres", len(df_filtrado))
    col2.metric("Áreas Auditadas", df_filtrado.get("Area Demandante", pd.Series()).nunique())
    col3.metric("Tipos de Documentos", df_filtrado.get("TIPO DOCUMENTO", pd.Series()).nunique())
    col4.metric("Níveis de Risco", df_filtrado.get("Risco_Tema", pd.Series()).nunique())

    st.divider()

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        if "Area Demandante" in df_filtrado.columns:
            st.markdown("**Volume de Pedidos por Área**")
            dados_area = df_filtrado["Area Demandante"].value_counts().reset_index()
            dados_area.columns = ['Area Demandante', 'Quantidade']
            # Mudando a cor do gráfico para um tom mais corporativo (Chumbo/Azul Escuro)
            fig_area = px.bar(dados_area, x="Area Demandante", y="Quantidade", text_auto=True, color_discrete_sequence=['#374151'])
            st.plotly_chart(fig_area, use_container_width=True)

    with col_graf2:
        if "Risco_Tema" in df_filtrado.columns:
            st.markdown("**Mapeamento de Nível de Risco**")
            # Paleta tradicional para riscos: Vermelho, Laranja, Verde, Azul, Roxo, Cinza
            cores_tradicionais = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#6b7280']
            
            fig_risco = px.pie(df_filtrado, names="Risco_Tema", hole=0.4, color_discrete_sequence=cores_tradicionais)
            st.plotly_chart(fig_risco, use_container_width=True)

    st.divider()
    
    st.markdown("### 📄 Rastreabilidade da Base de Dados")
    st.dataframe(df_filtrado, use_container_width=True)

    st.markdown("### 📥 Gerar Evidências (Exportar)")
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Auditoria_Compliance')
        
        st.download_button(
            label="📊 Descarregar Relatório (Excel)",
            data=buffer.getvalue(),
            file_name="evidencias_compliance.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with col_btn2:
        def gerar_pdf(dataframe):
            pdf = FPDF(orientation='L')
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Relatorio de Auditoria e Conformidade", ln=True, align='C')
            pdf.ln(5)
            
            colunas_pdf = list(dataframe.columns[:6]) 
            largura_col = 275 / len(colunas_pdf) if colunas_pdf else 275
            
            pdf.set_font("Arial", 'B', 8)
            for col in colunas_pdf:
                texto_col = str(col).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(largura_col, 8, texto_col, border=1)
            pdf.ln()
            
            pdf.set_font("Arial", size=8)
            for _, linha in dataframe.iterrows():
                for col in colunas_pdf:
                    texto_linha = str(linha[col])[:40] 
                    texto_limpo = texto_linha.encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(largura_col, 8, texto_limpo, border=1)
                pdf.ln()
                
            return pdf.output(dest='S').encode('latin-1')

        st.download_button(
            label="📄 Descarregar Relatório (PDF)",
            data=gerar_pdf(df_filtrado),
            file_name="evidencias_compliance.pdf",
            mime="application/pdf"
        )

else:
    st.info("👋 Bem-vindo ao sistema de auditoria contínua. Por favor, arraste o ficheiro de controlo (Excel) para a área de upload no menu lateral.")