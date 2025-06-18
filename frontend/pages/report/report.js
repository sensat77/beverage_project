// pages/report/report.js (最终语法修正版)
import { requestWithAuth } from '../../utils/api.js';

Page({
  data: {
    selectedMonth: '',
    summaryData: null,
    dailyBreakdown: [],
    isLoading: true
  },

  // 生命周期函数--监听页面加载
  onLoad: function (options) {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const defaultMonth = `${year}-${month}`;
    
    this.setData({
      selectedMonth: defaultMonth
    });
    this.fetchData(defaultMonth);
  },

  // 当用户通过picker选择了新的月份
  onMonthChange: function (e) {
    const newMonth = e.detail.value;
    this.setData({
      selectedMonth: newMonth
    });
    this.fetchData(newMonth);
  },

  // 获取数据的核心函数
  async fetchData(month) {
    this.setData({ isLoading: true, summaryData: null, dailyBreakdown: [] });
    try {
      const [summaryRes, breakdownRes] = await Promise.all([
        requestWithAuth({ url: `/api/monthly_summary?month=${month}` }),
        requestWithAuth({ url: `/api/reports/daily_breakdown?month=${month}` })
      ]);

      // 预格式化月度汇总数据
      if (summaryRes) {
        summaryRes.total_commission_str = (summaryRes.total_commission || 0).toFixed(2);
        summaryRes.total_display_fee_str = (summaryRes.total_display_fee || 0).toFixed(2);
        summaryRes.total_old_goods_disposal_fee_str = (summaryRes.total_old_goods_disposal_fee || 0).toFixed(2);
        summaryRes.total_gifting_cost_str = (summaryRes.total_gifting_cost || 0).toFixed(2);
      }

      this.setData({
        summaryData: summaryRes,
        dailyBreakdown: breakdownRes,
        isLoading: false
      });

    } catch (error) {
      console.error("加载报表数据失败:", error);
      wx.showToast({ title: '加载失败', icon: 'none' });
      this.setData({ isLoading: false });
    }
  },

  // 点击某一天进行跳转的函数
  onDayTap: function(e) {
    const day = e.currentTarget.dataset.day;
    const fullDate = `${this.data.selectedMonth}-${day.toString().padStart(2, '0')}`;
    wx.navigateTo({
      url: `/pages/daily_orders/daily_orders?date=${fullDate}`
    });
  } // <-- 这是最后一个函数，它的末尾不需要逗号
});