import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import base64
from fpdf import FPDF

# Configuração da página
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
            border-left: 5px solid #1f2937;
        }
        
        div[data-testid="metric-container"]:hover {
            transform: scale(1.02);
            box-shadow: 4px 4px 15px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN CENTRALIZADO (COM SECRETS) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    
    col1, col2, col3 = st.columns([1, 1.5, 1]) 
    
    with col2:
        st.write("") 
        st.write("") 

        if os.path.exists("logo_light.png") and os.path.exists("logo_dark.png"):
            with open("logo_light.png", "rb") as f:
                img_light = base64.b64encode(f.read()).decode()
            with open("logo_dark.png", "rb") as f:
                img_dark = base64.b64encode(f.read()).decode()
                
            st.markdown(f"""
                <div>
                    <style>
                        .img-logo-login {{ 
                            max-width: 250px; 
                            height: auto; 
                            margin-left: 100px; 
                        }}
                        .modo-claro {{ display: block; }}
                        .modo-escuro {{ display: none; }}
                        @media (prefers-color-scheme: dark) {{
                            .modo-claro {{ display: none !important; }}
                            .modo-escuro {{ display: block !important; }}
                        }}
                    </style>
                    <img src="data:image/png;base64,{img_light}" class="img-logo-login modo-claro">
                    <img src="data:image/png;base64,{img_dark}" class="img-logo-login modo-escuro">
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='width: 100%; text-align: center; color: gray; margin-bottom: 20px;'>[ ESPAÇO PARA A SUA LOGO ]</div>", unsafe_allow_html=True)

        st.markdown("<h2 style='text-align: center;'>🔒 Acesso Restrito</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Bem-vindo ao Sistema de Compliance. Por favor, insira as suas credenciais.</p>", unsafe_allow_html=True)
        st.divider()
        
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password") 
        btn_login = st.button("Entrar no Sistema", use_container_width=True)
        
        if btn_login:
            # Lendo a senha segura do Streamlit Cloud
            if usuario == st.secrets["USUARIO"] and senha == st.secrets["SENHA"]:
                st.session_state["autenticado"] = True
                st.rerun() 
            else:
                st.error("❌ Usuário ou senha incorretos.")
    
    st.stop() 


# ==========================================
# SEU CÓDIGO DO PAINEL (PROTEGIDO)
# ==========================================

if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

st.title("⚖️ Sistema Analítico de Compliance")
st.markdown("Monitorização de **Governança, Riscos e Conformidade (GRC)**")
st.divider()

if os.path.exists("logo_light.png") and os.path.exists("logo_dark.png"):
    with open("logo_light.png", "rb") as f:
        light_b64 = base64.b64encode(f.read()).decode()
    with open("logo_dark.png", "rb") as f:
        dark_b64 = base64.b64encode(f.read()).decode()
        
    st.sidebar.markdown(f"""
        <style>
            .logo-sidebar-light {{ display: block; width: 100%; margin-bottom: 15px; }}
            .logo-sidebar-dark {{ display: none; width: 100%; margin-bottom: 15px; }}
            @media (prefers-color-scheme: dark) {{
                .logo-sidebar-light {{ display: none; }}
                .logo-sidebar-dark {{ display: block; }}
            }}
        </style>
        <img src="data:image/png;base64,{light_b64}" class="logo-sidebar-light">
        <img src="data:image/png;base64,{dark_b64}" class="logo-sidebar-dark">
    """, unsafe_allow_html=True)

st.sidebar.markdown("### 🛡️ Governança e Risco")
ficheiro_upload = st.sidebar.file_uploader("Carregar ficheiro (.xlsx)", type=["xlsx"])

if ficheiro_upload is not None:
    
    @st.cache_data
    def processar_planilha(ficheiro):
        df = pd.read_excel(ficheiro)
        df.columns = df.columns.str.strip() 
        return df

    df = processar_planilha(ficheiro_upload)
    st.sidebar.divider()
    
    # ==========================================
    # NOVO: SISTEMA DE FILTROS DINÂMICOS
    # ==========================================
    st.sidebar.header("🔍 Filtros Dinâmicos")
    
    # 1. Busca por Número do Processo (Fixo, porque é busca de texto livre)
    filtro_num = st.sidebar.text_input("Procurar por Número de Processo (Opcional)")
    df_filtrado = df.copy()
    
    if filtro_num and "Num_Processo" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Num_Processo"].astype(str).str.contains(filtro_num, case=False, na=False)]

    # 2. Descobre todas as colunas que existem na planilha
    todas_as_colunas = df.columns.tolist()
    
    # Tenta pré-selecionar as colunas antigas, se elas existirem no arquivo
    colunas_sugeridas = [col for col in ["TIPO DOCUMENTO", "Area Demandante", "Status", "Risco_Tema", "Resultado"] if col in todas_as_colunas]

    # 3. O usuário escolhe quais colunas quer transformar em filtro!
    colunas_escolhidas = st.sidebar.multiselect(
        "⚙️ Escolha as colunas para filtrar:", 
        options=todas_as_colunas, 
        default=colunas_sugeridas
    )
    
    st.sidebar.markdown("---")

    # 4. Cria os filtros reais baseado no que o usuário escolheu acima
    for coluna in colunas_escolhidas:
        valores_unicos = df[coluna].dropna().unique().tolist()
        selecao_usuario = st.sidebar.multiselect(f"Filtrar por: {coluna}", valores_unicos)
        
        # Se o usuário marcar algo no filtro, a tabela corta os dados
        if selecao_usuario:
            df_filtrado = df_filtrado[df_filtrado[coluna].isin(selecao_usuario)]

    # ==========================================
    # FIM DOS FILTROS DINÂMICOS
    # ==========================================

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
            fig_area = px.bar(dados_area, x="Area Demandante", y="Quantidade", text_auto=True, color_discrete_sequence=['#374151'])
            st.plotly_chart(fig_area, use_container_width=True)

    with col_graf2:
        if "Risco_Tema" in df_filtrado.columns:
            st.markdown("**Mapeamento de Nível de Risco**")
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
    st.info("👋 Bem-vindo ao sistema. Por favor, arraste o ficheiro de controlo (Excel) para a área de upload no menu lateral.")