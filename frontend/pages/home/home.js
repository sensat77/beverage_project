// pages/home/home.js (修正版)
import { requestWithAuth } from '../../utils/api.js';

const formatDate = date => {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

Page({
  data: {
    summaryData: null,
    // orderList: [], // 【删除】不再需要最近订单列表
    userInfo: null, 
    isLoading: true,
    selectedDate: formatDate(new Date()), // 默认选中今天

    topProductsSales: [] // 【新增】重点产品销售数据
  },

  onShow: function () {
    this.fetchData();
  },

  onPullDownRefresh: function () {
    this.fetchData();
  },

  onDateChange: function (e) {
    this.setData({
      selectedDate: e.detail.value
    });
    this.fetchData();
  },

  goToToday: function() {
    const today = new Date();
    const todayFormatted = formatDate(today);
    if (this.data.selectedDate !== todayFormatted) {
      this.setData({
        selectedDate: todayFormatted
      }, () => {
        this.fetchData();
      });
    } else {
      wx.showToast({
        title: '已是今日',
        icon: 'none'
      });
      this.fetchData(); // 强制刷新
    }
  },

  fetchData: async function () {
    this.setData({ isLoading: true });
    const date = this.data.selectedDate;
  
    try {
      // 【修改】只请求 daily_summary 和 profile，并新增 top_product_sales
      const [summaryRes, profileRes, topProductsRes] = await Promise.all([
        requestWithAuth({ url: `/api/daily_summary?date=${date}` }),
        requestWithAuth({ url: '/api/profile' }),
        // 【新增】调用获取重点产品销售数据的新接口
        requestWithAuth({ url: `/api/reports/top_product_sales?date=${date}` }) 
      ]);
  
      // --- 预格式化 “速览” 卡片中的金额 ---
      if (summaryRes) {
        summaryRes.total_commission_str = (summaryRes.total_commission || 0).toFixed(2);
        summaryRes.total_gifting_cost_str = (summaryRes.total_gifting_cost || 0).toFixed(2);
        summaryRes.total_display_fee_str = (summaryRes.total_display_fee || 0).toFixed(2);
        summaryRes.total_old_goods_disposal_fee_str = (summaryRes.total_old_goods_disposal_fee || 0).toFixed(2);
      }
  
      this.setData({
        summaryData: summaryRes,
        // orderList: [], // 【删除】清空 orderList 数据
        userInfo: profileRes, 
        topProductsSales: topProductsRes, // 【新增】设置重点产品销售数据
        isLoading: false
      });
  
    } catch (error) {
      console.error("获取首页数据失败:", error);
      wx.showToast({ title: '数据加载失败', icon: 'none' });
      this.setData({ isLoading: false });
    } finally {
      wx.stopPullDownRefresh();
    }
  },

  // 【删除】onOrderTap 函数，因为不再显示最近订单
  // onOrderTap: function(e) {
  //   const orderId = e.currentTarget.dataset.orderid;
  //   wx.navigateTo({
  //     url: `/pages/order_detail/order_detail?id=${orderId}`
  //   });
  // },

  goToInputPage: function () {
    wx.navigateTo({
      url: '/pages/input/input'
    });
  }
})