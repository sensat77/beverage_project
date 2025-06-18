// pages/daily_orders/daily_orders.js (最终完整版)
import { requestWithAuth } from '../../utils/api.js';

Page({
  data: {
    orderList: [],
    targetDate: '',
    isLoading: true,
  },

  onLoad: function (options) {
    const date = options.date;
    if (date) {
      this.setData({ targetDate: date });
      wx.setNavigationBarTitle({ title: `${date} 订单列表` });
      this.fetchOrders(date);
    }
  },

  async fetchOrders(date) {
    this.setData({ isLoading: true });
    try {
      const res = await requestWithAuth({ url: `/api/reports/orders_by_date?date=${date}` });
      if (res) {
        // 预格式化提成金额
        res.forEach(o => o.total_commission_str = (o.total_commission || 0).toFixed(2));
      }
      this.setData({ orderList: res || [] });
    } catch (error) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ isLoading: false });
    }
  },

  // 点击订单项，跳转到详情页
  onOrderTap(e) {
    const orderId = e.currentTarget.dataset.orderid;
    wx.navigateTo({
      url: `/pages/order_detail/order_detail?id=${orderId}`
    });
  },

  // 点击删除按钮
  onDeleteOrder(e) {
    const { orderid, index } = e.currentTarget.dataset;
    wx.showModal({
      title: '确认删除',
      content: `您确定要永久删除这笔订单吗？此操作无法撤销。`,
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          try {
            // 调用后端的DELETE API
            await requestWithAuth({ url: `/api/reports/order/${orderid}`, method: 'DELETE' });
            wx.hideLoading();
            wx.showToast({ title: '删除成功' });

            // 从界面上直接移除这一项，避免重新刷新页面
            let newList = this.data.orderList;
            newList.splice(index, 1);
            this.setData({ orderList: newList });

          } catch (error) {
            wx.hideLoading();
            wx.showToast({ title: '删除失败', icon: 'none' });
          }
        }
      }
    });
  }
})