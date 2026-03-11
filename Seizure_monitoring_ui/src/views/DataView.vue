<template>
  <div class="data-visualization-container">
    <!-- 顶部标题栏 -->
    <div class="header">
      <div class="title">
        <span class="main-title">医疗数据可视化平台</span>
        <span class="sub-title">实时监控 · 智能分析 · 辅助决策</span>
      </div>
      <div class="time-info">
        <span class="date">{{ currentDate }}</span>
        <span class="time">{{ currentTime }}</span>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <!-- 患者统计卡片 -->
        <div class="data-card patient-stats">
          <div class="card-header">
            <span class="card-title">患者统计</span>
            <el-tag size="small" effect="dark" type="primary">实时数据</el-tag>
          </div>
          <div class="card-content">
            <div class="stat-item">
              <div class="stat-value">{{ patientStats.total }}</div>
              <div class="stat-label">总患者数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ patientStats.inpatient }}</div>
              <div class="stat-label">住院患者</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ patientStats.outpatient }}</div>
              <div class="stat-label">门诊患者</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ patientStats.emergency }}</div>
              <div class="stat-label">急诊患者</div>
            </div>
          </div>
          <div id="patient-trend-chart" class="chart-container"></div>
        </div>

        <!-- 科室负荷卡片 -->
        <div class="data-card department-load">
          <div class="card-header">
            <span class="card-title">科室负荷</span>
            <el-tag size="small" effect="dark" type="success">实时监控</el-tag>
          </div>
          <div id="department-load-chart" class="chart-container"></div>
        </div>
      </div>

      <!-- 中间面板 -->
      <div class="center-panel">
        <!-- 地理分布图 -->
        <div class="data-card geo-distribution">
          <div class="card-header">
            <span class="card-title">西北地区医疗资源分布</span>
            <div class="legend">
              <span class="legend-item"><i class="legend-color" style="background-color: #5470c6;"></i>三甲医院</span>
              <span class="legend-item"><i class="legend-color" style="background-color: #91cc75;"></i>医疗卫生机构床位</span>
              <span class="legend-item"><i class="legend-color" style="background-color: #fac858;"></i>卫生技术人员</span>
            </div>
          </div>
          <div id="geo-map" class="map-container"></div>
          
          <!-- 添加数据表格 -->
          <div class="data-table">
            <el-table :data="northwestMedicalData" size="small" border stripe>
              <el-table-column prop="province" label="省份" width="100"></el-table-column>
              <el-table-column prop="hospitals" label="三甲医院数量" width="120"></el-table-column>
              <el-table-column prop="beds" label="医疗卫生机构床位数(万张)"></el-table-column>
              <el-table-column prop="staff" label="卫生技术人员(万人)"></el-table-column>
              <el-table-column prop="bedsPerThousand" label="每千人床位数"></el-table-column>
              <el-table-column prop="staffPerThousand" label="每千人卫生技术人员"></el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 实时监控数据 -->
        <div class="data-card realtime-monitor">
          <div class="card-header">
            <span class="card-title">重症监护实时数据</span>
            <el-tag size="small" effect="dark" type="danger">高优先级</el-tag>
          </div>
          <div class="monitor-grid">
            <div class="monitor-item" v-for="(item, index) in monitorData" :key="index">
              <div class="monitor-header">
                <span class="monitor-title">{{ item.name }}</span>
                <span class="monitor-status" :class="item.status">{{ item.statusText }}</span>
              </div>
              <div class="monitor-value">{{ item.value }}{{ item.unit }}</div>
              <div class="monitor-chart" :id="`monitor-chart-${index}`"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="right-panel">
        <!-- 疾病趋势卡片 -->
        <div class="data-card disease-trend">
          <div class="card-header">
            <span class="card-title">疾病趋势分析</span>
            <el-select v-model="selectedDisease" size="small" placeholder="选择疾病类型">
              <el-option v-for="item in diseaseOptions" :key="item.value" :label="item.label" :value="item.value">
              </el-option>
            </el-select>
          </div>
          <div id="disease-trend-chart" class="chart-container"></div>
        </div>

        <!-- 医疗资源使用率 -->
        <div class="data-card resource-usage">
          <div class="card-header">
            <span class="card-title">医疗资源使用率</span>
          </div>
          <div class="resource-list">
            <div class="resource-item" v-for="(item, index) in resourceUsage" :key="index">
              <div class="resource-info">
                <span class="resource-name">{{ item.name }}</span>
                <span class="resource-percent">{{ item.percent }}%</span>
              </div>
              <el-progress :percentage="item.percent" :color="getProgressColor(item.percent)" :stroke-width="8" />
            </div>
          </div>
        </div>

        <!-- 预警信息 -->
        <div class="data-card alert-info">
          <div class="card-header">
            <span class="card-title">系统预警</span>
            <el-tag size="small" effect="dark" type="warning">{{ alerts.length }}条未处理</el-tag>
          </div>
          <div class="alert-list">
            <div class="alert-item" v-for="(item, index) in alerts" :key="index" :class="item.level">
              <div class="alert-time">{{ item.time }}</div>
              <div class="alert-content">{{ item.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import 'echarts/extension/bmap/bmap'
import axios from 'axios'

// 西北地区医疗数据
const northwestMedicalData = ref([
  { 
    province: '陕西省', 
    hospitals: '50+', 
    beds: 27.3, 
    staff: 36.9, 
    bedsPerThousand: 6.9, 
    staffPerThousand: 9.3,
    value: 50
  },
  { 
    province: '甘肃省', 
    hospitals: '20+', 
    beds: 16.8, 
    staff: 17.5, 
    bedsPerThousand: 6.7, 
    staffPerThousand: 7.0,
    value: 20
  },
  { 
    province: '青海省', 
    hospitals: '10', 
    beds: 4.1, 
    staff: 4.8, 
    bedsPerThousand: 6.9, 
    staffPerThousand: 8.2,
    value: 10
  },
  { 
    province: '宁夏', 
    hospitals: '8', 
    beds: 4.2, 
    staff: 5.4, 
    bedsPerThousand: 5.8, 
    staffPerThousand: 7.5,
    value: 8
  },
  { 
    province: '新疆', 
    hospitals: '35+', 
    beds: 17.8, 
    staff: 20.3, 
    bedsPerThousand: 7.0, 
    staffPerThousand: 8.0,
    value: 35
  }
])

// 时间相关
const currentDate = ref(new Date().toLocaleDateString())
const currentTime = ref(new Date().toLocaleTimeString())
let timer = null

// 更新时间
const updateTime = () => {
  const now = new Date()
  currentDate.value = now.toLocaleDateString()
  currentTime.value = now.toLocaleTimeString()
}

// 患者统计数据
const patientStats = ref({
  total: 2458,
  inpatient: 632,
  outpatient: 1685,
  emergency: 141
})

// 监控数据
const monitorData = ref([
  { name: '心率', value: 85, unit: 'bpm', status: 'normal', statusText: '正常', data: generateRandomData(20, 70, 90) },
  { name: '血压', value: '120/80', unit: 'mmHg', status: 'normal', statusText: '正常', data: generateRandomData(20, 110, 130) },
  { name: '血氧', value: 98, unit: '%', status: 'normal', statusText: '正常', data: generateRandomData(20, 95, 100) },
  { name: '体温', value: 36.5, unit: '°C', status: 'normal', statusText: '正常', data: generateRandomData(20, 36, 37) }
])

// 疾病选项
const selectedDisease = ref('respiratory')
const diseaseOptions = [
  { value: 'respiratory', label: '呼吸系统疾病' },
  { value: 'cardiovascular', label: '心血管疾病' },
  { value: 'digestive', label: '消化系统疾病' },
  { value: 'neurological', label: '神经系统疾病' }
]

// 医疗资源使用率
const resourceUsage = ref([
  { name: '病床使用率', percent: 78 },
  { name: '医护人员配置', percent: 92 },
  { name: '医疗设备使用率', percent: 65 },
  { name: '药品库存水平', percent: 83 },
  { name: 'ICU使用率', percent: 88 }
])

// 预警信息
const alerts = ref([
  { time: '10:25', content: 'ICU-3号床患者血氧水平下降', level: 'critical' },
  { time: '09:40', content: '急诊科患者等待时间超过30分钟', level: 'warning' },
  { time: '08:15', content: '药房抗生素库存不足', level: 'normal' },
  { time: '07:30', content: '2号手术室设备维护提醒', level: 'normal' }
])

// 生成随机数据
function generateRandomData(count, min, max) {
  const result = []
  for (let i = 0; i < count; i++) {
    result.push(Math.floor(Math.random() * (max - min + 1)) + min)
  }
  return result
}

// 获取进度条颜色
const getProgressColor = (percent) => {
  if (percent < 60) return '#67C23A'
  if (percent < 80) return '#E6A23C'
  return '#F56C6C'
}

// 初始化图表
const initCharts = () => {
  // 患者趋势图表
  const patientTrendChart = echarts.init(document.getElementById('patient-trend-chart'))
  patientTrendChart.setOption({
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      top: 10,
      right: 10,
      bottom: 20,
      left: 40
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '患者数量',
        type: 'line',
        smooth: true,
        data: [320, 302, 341, 374, 390, 450, 420],
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(80, 141, 255, 0.8)' },
              { offset: 1, color: 'rgba(80, 141, 255, 0.1)' }
            ]
          }
        },
        lineStyle: {
          width: 3,
          color: '#508DFF'
        },
        symbol: 'circle',
        symbolSize: 8
      }
    ]
  })

  // 科室负荷图表
  const departmentLoadChart = echarts.init(document.getElementById('department-load-chart'))
  departmentLoadChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      top: 10,
      right: 10,
      bottom: 20,
      left: 80
    },
    xAxis: {
      type: 'value',
      max: 100
    },
    yAxis: {
      type: 'category',
      data: ['儿科', '内科', '外科', '妇产科', '急诊科', '神经科', '心脏科']
    },
    series: [
      {
        name: '负荷率',
        type: 'bar',
        data: [85, 72, 68, 90, 95, 60, 78],
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%'
        },
        itemStyle: {
          color: function(params) {
            const value = params.value
            if (value > 90) return '#F56C6C'
            if (value > 70) return '#E6A23C'
            return '#67C23A'
          }
        }
      }
    ]
  })

  // 地理分布图 - 修改为西北地区地图
  const geoMap = echarts.init(document.getElementById('geo-map'))
  geoMap.setOption({
    title: {
      text: '西北地区医疗资源分布',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        const data = northwestMedicalData.value.find(item => item.province.includes(params.name) || params.name.includes(item.province));
        if (data) {
          return `<div style="font-weight:bold;margin-bottom:5px;">${params.name}</div>
                  <div>三甲医院数量：${data.hospitals}</div>
                  <div>医疗卫生机构床位数：${data.beds}万张</div>
                  <div>卫生技术人员：${data.staff}万人</div>
                  <div>每千人床位数：${data.bedsPerThousand}</div>
                  <div>每千人卫生技术人员：${data.staffPerThousand}</div>`;
        }
        return params.name;
      }
    },
    visualMap: {
      min: 0,
      max: 50,
      text: ['高', '低'],
      realtime: false,
      calculable: true,
      inRange: {
        color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695']
      }
    },
    series: [
      {
        name: '三甲医院数量',
        type: 'map',
        map: 'china',
        roam: true,
        zoom: 1.5,
        center: [103, 36], // 将地图中心设置在西北地区
        selectedMode: 'single',
        emphasis: {
          label: {
            show: true
          }
        },
        select: {
          label: {
            show: true
          }
        },
        data: [
          {name: '陕西', value: 50},
          {name: '甘肃', value: 20},
          {name: '青海', value: 10},
          {name: '宁夏', value: 8},
          {name: '新疆', value: 35}
        ]
      }
    ]
  });
  
  // 添加地图点击事件，可以查看各省详情
  geoMap.on('click', function(params) {
    const provinceName = params.name;
    const provinceMap = {
      '陕西': 'shanxi1',
      '甘肃': 'gansu',
      '青海': 'qinghai',
      '宁夏': 'ningxia',
      '新疆': 'xinjiang'
    };
    
    if (provinceMap[provinceName]) {
      showProvinceDetail(geoMap, provinceName, provinceMap[provinceName]);
    }
  });

  // 疾病趋势图表
  const diseaseTrendChart = echarts.init(document.getElementById('disease-trend-chart'))
  diseaseTrendChart.setOption({
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['确诊病例', '治愈病例'],
      top: 10
    },
    grid: {
      top: 40,
      right: 20,
      bottom: 20,
      left: 40
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '确诊病例',
        type: 'line',
        stack: 'Total',
        data: [120, 132, 101, 134, 90, 230],
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#F56C6C'
        }
      },
      {
        name: '治愈病例',
        type: 'line',
        stack: 'Total',
        data: [80, 100, 90, 120, 80, 210],
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#67C23A'
        }
      }
    ]
  })

  // 监控小图表
  monitorData.value.forEach((item, index) => {
    const chart = echarts.init(document.getElementById(`monitor-chart-${index}`))
    chart.setOption({
      grid: {
        top: 0,
        right: 0,
        bottom: 0,
        left: 0
      },
      xAxis: {
        type: 'category',
        show: false,
        data: Array.from({ length: item.data.length }, (_, i) => i)
      },
      yAxis: {
        type: 'value',
        show: false
      },
      series: [
        {
          data: item.data,
          type: 'line',
          showSymbol: false,
          smooth: true,
          lineStyle: {
            width: 2,
            color: getMonitorColor(item.status)
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: getMonitorColor(item.status, 0.2) },
                { offset: 1, color: getMonitorColor(item.status, 0.01) }
              ]
            }
          }
        }
      ]
    })
  })
}

// 获取监控图表颜色
const getMonitorColor = (status, alpha = 1) => {
  const colors = {
    normal: `rgba(103, 194, 58, ${alpha})`,
    warning: `rgba(230, 162, 60, ${alpha})`,
    critical: `rgba(245, 108, 108, ${alpha})`
  }
  return colors[status] || colors.normal
}

// 窗口大小变化时重新调整图表
const resizeCharts = () => {
  const charts = document.querySelectorAll('.chart-container, .monitor-chart, .map-container')
  charts.forEach(chart => {
    const instance = echarts.getInstanceByDom(chart)
    instance && instance.resize()
  })
}

// 生命周期钩子
onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  
  // 初始化图表
  setTimeout(() => {
    initCharts()
    window.addEventListener('resize', resizeCharts)
  }, 100)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  window.removeEventListener('resize', resizeCharts)
  
  // 销毁图表实例
  const charts = document.querySelectorAll('.chart-container, .monitor-chart, .map-container')
  charts.forEach(chart => {
    const instance = echarts.getInstanceByDom(chart)
    instance && instance.dispose()
  })
})
</script>

<style scoped>
.data-visualization-container {
  width: 100%;
  height: 100vh;
  background-color: #f0f2f5;
  color: #333;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 顶部标题栏 */
.header {
  height: 60px;
  background: linear-gradient(90deg, #1976d2, #2196f3);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.title {
  display: flex;
  flex-direction: column;
}

.main-title {
  font-size: 20px;
  font-weight: bold;
}

.sub-title {
  font-size: 12px;
  opacity: 0.8;
}

.time-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.date, .time {
  font-size: 14px;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: flex;
  padding: 15px;
  gap: 15px;
  overflow: hidden;
}

/* 面板样式 */
.left-panel, .right-panel {
  width: 25%;
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
}

.center-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
}

/* 卡片样式 */
.data-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 15px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

/* 患者统计卡片 */
.patient-stats .card-content {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

/* 图表容器 */
.chart-container {
  flex: 1;
  min-height: 200px;
}

.map-container {
  flex: 1;
  min-height: 400px;
}

/* 监控数据 */
.monitor-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.monitor-item {
  background-color: #f9f9f9;
  border-radius: 6px;
  padding: 10px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.monitor-title {
  font-size: 14px;
  color: #606266;
}

.monitor-status {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 10px;
}

.monitor-status.normal {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67C23A;
}

.monitor-status.warning {
  background-color: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
}

.monitor-status.critical {
  background-color: rgba(245, 108, 108, 0.1);
  color: #F56C6C;
}

.monitor-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.monitor-chart {
  height: 50px;
}

/* 资源使用率 */
.resource-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.resource-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.resource-info {
  display: flex;
  justify-content: space-between;
}

.resource-name {
  font-size: 14px;
  color: #606266;
}

.resource-percent {
  font-size: 14px;
  font-weight: bold;
}

/* 预警信息 */
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  padding: 10px;
  border-radius: 6px;
  display: flex;
  align-items: center;
}

.alert-item.critical {
  background-color: rgba(245, 108, 108, 0.1);
  border-left: 4px solid #F56C6C;
}

.alert-item.warning {
  background-color: rgba(230, 162, 60, 0.1);
  border-left: 4px solid #E6A23C;
}

.alert-item.normal {
  background-color: rgba(144, 147, 153, 0.1);
  border-left: 4px solid #909399;
}

.alert-time {
  font-size: 12px;
  color: #909399;
  margin-right: 10px;
  min-width: 40px;
}

.alert-content {
  font-size: 14px;
  color: #606266;
}

/* 图例样式 */
.legend {
  display: flex;
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.legend-color {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 5px;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>