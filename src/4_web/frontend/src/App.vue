<template>
  <div id="app" style="font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px;">
    <h1>Intuitive Care - Monitoramento de Operadoras</h1>
    
    <div style="margin-bottom: 20px;">
      <button @click="currentTab = 'table'" :class="{ active: currentTab === 'table' }">Tabela de Operadoras</button>
      <button @click="currentTab = 'chart'" :class="{ active: currentTab === 'chart' }">Gráfico por UF</button>
    </div>

    <!-- Tabela -->
    <div v-if="currentTab === 'table'">
      <div style="margin-bottom: 10px;">
        <input v-model="searchQuery" placeholder="Buscar por Razão Social ou CNPJ" @input="fetchOperadoras" style="padding: 8px; width: 300px;">
      </div>
      
      <table border="1" cellpadding="10" cellspacing="0" style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr style="background-color: #f2f2f2;">
            <th>Registro ANS</th>
            <th>CNPJ</th>
            <th>Razão Social</th>
            <th>UF</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="op in operadoras" :key="op.registro_ans">
            <td>{{ op.registro_ans }}</td>
            <td>{{ op.cnpj }}</td>
            <td>{{ op.razao_social }}</td>
            <td>{{ op.uf }}</td>
            <td>
              <button @click="verDetalhes(op)">Ver Despesas</button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div style="margin-top: 10px;">
        <button @click="page--; fetchOperadoras()" :disabled="page <= 1">Anterior</button>
        <span style="margin: 0 10px;">Página {{ page }}</span>
        <button @click="page++; fetchOperadoras()">Próxima</button>
      </div>

      <!-- Modal Detalhes -->
      <div v-if="selectedOperadora" class="modal">
        <div class="modal-content">
          <span class="close" @click="selectedOperadora = null">&times;</span>
          <h2>{{ selectedOperadora.razao_social }}</h2>
          <p>CNPJ: {{ selectedOperadora.cnpj }}</p>
          <h3>Histórico de Despesas</h3>
          <ul>
            <li v-for="(desp, index) in despesas" :key="index">
              {{ desp.ano }}/{{ desp.trimestre }}: R$ {{ desp.valor_despesas }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Gráfico (Placeholder Visual) -->
    <div v-if="currentTab === 'chart'">
      <h2>Distribuição de Despesas por UF</h2>
      <p><i>(Este componente renderizaria um gráfico Chart.js consumindo /api/estatisticas)</i></p>
      <div style="display: flex; gap: 10px; align-items: flex-end; height: 300px; border-bottom: 2px solid #333;">
        <div v-for="stat in stats" :key="stat.uf" :style="{ height: (stat.total_despesas / maxDespesa * 200) + 'px', background: 'blue', width: '50px', textAlign: 'center', color: 'white' }">
          {{ stat.uf }}
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'App',
  data() {
    return {
      currentTab: 'table',
      operadoras: [],
      searchQuery: '',
      page: 1,
      selectedOperadora: null,
      despesas: [],
      stats: [],
      maxDespesa: 1
    }
  },
  mounted() {
    this.fetchOperadoras();
    this.fetchStats();
  },
  methods: {
    async fetchOperadoras() {
      try {
        const res = await axios.get(`http://localhost:8000/api/operadoras`, {
          params: { page: this.page, search: this.searchQuery }
        });
        this.operadoras = res.data;
      } catch (error) {
        console.error("Erro ao buscar operadoras", error);
        // Mock data para visualização se API estiver off
        this.operadoras = [
            { registro_ans: '123456', cnpj: '00.000.000/0001-00', razao_social: 'EXEMPLO OPERADORA SA', uf: 'SP' },
            { registro_ans: '654321', cnpj: '99.999.999/0001-99', razao_social: 'TESTE SAUDE LTDA', uf: 'RJ' }
        ];
      }
    },
    async verDetalhes(op) {
      this.selectedOperadora = op;
      try {
        const res = await axios.get(`http://localhost:8000/api/operadoras/${op.registro_ans}/despesas`);
        this.despesas = res.data;
      } catch (error) {
        this.despesas = [{ ano: 2023, trimestre: '1T', valor_despesas: 150000.00 }];
      }
    },
    async fetchStats() {
      try {
        const res = await axios.get(`http://localhost:8000/api/estatisticas`);
        this.stats = res.data.slice(0, 10); // Top 10
        this.maxDespesa = Math.max(...this.stats.map(s => s.total_despesas)) || 1;
      } catch (error) {
        this.stats = [{ uf: 'SP', total_despesas: 5000 }, { uf: 'RJ', total_despesas: 3000 }];
        this.maxDespesa = 5000;
      }
    }
  }
}
</script>

<style>
button { padding: 10px 20px; cursor: pointer; margin-right: 5px; }
button.active { background-color: #007bff; color: white; border: none; }
.modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; }
.modal-content { background: white; padding: 20px; border-radius: 5px; width: 500px; }
.close { float: right; cursor: pointer; font-size: 20px; }
</style>
