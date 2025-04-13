import streamlit as st
import requests
from datetime import datetime, timedelta

st.title("Simulador Delta Neutro: Short Perp + Long Futuro (Binance)")

# --- Configurações iniciais ---
PERP_SYMBOL = "BTCUSDT"
FUTURE_SYMBOL = "BTCUSD_240628"  # Ajuste conforme o contrato trimestral vigente

# --- Funções auxiliares ---
def get_price(symbol, is_futures=False):
    url = "https://fapi.binance.com/fapi/v1/ticker/price" if is_futures else "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url, params={"symbol": symbol})
    data = response.json()
    if 'price' in data:
        return float(data['price'])
    else:
        st.error(f"Erro ao buscar preço para {symbol}: {data}")
        st.stop()

def get_funding(symbol):
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    params = {"symbol": symbol, "limit": 8}  # últimos 8 períodos = 24h
    response = requests.get(url, params=params).json()
    funding_rates = [float(entry['fundingRate']) for entry in response]
    return sum(funding_rates), funding_rates[-1]  # acumulado 24h, atual

def get_fee():
    return 0.0004  # 0.04% por trade (padrão na Binance)

# --- Obter dados ---
with st.spinner("Carregando dados da Binance..."):
    perp_price = get_price(PERP_SYMBOL)
    future_price = get_price(FUTURE_SYMBOL, is_futures=True)
    funding_24h, current_funding = get_funding(PERP_SYMBOL)
    fee = get_fee()

# --- Exibir dados ---
st.subheader("Dados do Mercado (Binance)")
st.write(f"**Preço Perpétuo:** ${perp_price:,.2f}")
st.write(f"**Preço Futuro (Trimestral):** ${future_price:,.2f}")
st.write(f"**Basis Atual:** ${future_price - perp_price:,.2f}")
st.write(f"**Funding Atual (8h):** {current_funding*100:.4f}%")
st.write(f"**Funding Acumulado 24h:** {funding_24h*100:.4f}%")

# --- Simulação ---
st.subheader("Simulação de PnL")
position_size = st.number_input("Tamanho da posição (BTC)", 0.01, 10.0, 1.0)
vencimento = datetime(2024, 6, 28)
dias_restantes = (vencimento - datetime.utcnow()).days
funding_por_dia = funding_24h / 1
funding_total = funding_por_dia * dias_restantes

# Cálculos
basis = future_price - perp_price
funding_recebido_usd = funding_total * perp_price * position_size
lucro_total = funding_recebido_usd - basis * position_size
custo_taxas = fee * perp_price * 2 * position_size
lucro_liquido = lucro_total - custo_taxas
roi = (lucro_liquido / (perp_price * position_size)) * 100

# --- Resultados ---
st.write(f"**Funding estimado até o vencimento:** {funding_total*100:.2f}%")
st.write(f"**Recebimento em funding (USDT):** ${funding_recebido_usd:,.2f}")
st.write(f"**Perda com basis (USDT):** ${basis * position_size:,.2f}")
st.write(f"**Taxas totais estimadas (USDT):** ${custo_taxas:,.2f}")
st.success(f"**Lucro líquido estimado:** ${lucro_liquido:,.2f} | ROI: {roi:.2f}%")
