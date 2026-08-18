"""
Settings Page — US-9.5 (Placeholder)
"""
import streamlit as st


def show() -> None:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    st.markdown("""
    <div class="glass-card">
        <h3 style="color:#6366f1; margin-top:0">🚧 Coming Soon</h3>
        <p style="color:#94a3b8">
            This page will let you configure platform settings without editing files.
            For now, all credentials are managed via the <code>.env</code> file.
        </p>
    </div>
    """, unsafe_allow_html=True)

    items = [
        ("🐘", "PostgreSQL / MySQL Connection", "Host, port, credentials for your database connectors."),
        ("🕷️", "Firecrawl API Key", "Your Firecrawl key for web scraping (`FIRECRAWL_API_KEY`)."),
        ("🤖", "n8n Webhook URL", "Endpoint for the automated pipeline scheduler (`N8N_HOST`)."),
        ("📅", "Default Experiment Schedule", "Cron expression for auto-retraining (`run_end_to_end_pipeline`)."),
        ("🔐", "Encryption Key", "Fernet key used to encrypt stored connector passwords (`ENCRYPTION_KEY`)."),
        ("📊", "ML Model Directory", "Where serialized model artifacts are saved (`MODEL_DIR`)."),
    ]

    st.markdown("### What you'll be able to configure here:")
    for icon, title, description in items:
        st.markdown(f"""
        <div class="glass-card" style="padding:16px 20px; margin-bottom:12px;">
            <span style="font-size:1.2rem">{icon}</span>
            <strong style="margin-left:10px; color:#e2e8f0">{title}</strong>
            <br>
            <span style="color:#64748b; font-size:0.88rem; margin-left:32px">{description}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2);
                border-radius:12px; padding:16px 20px; color:#94a3b8; font-size:0.9rem">
        📋 <strong style="color:#818cf8">For this capstone</strong>, credentials are configured
        via the <code>.env</code> file in the project root.
        See <code>.env.example</code> for all available settings.
    </div>
    """, unsafe_allow_html=True)
