# EX
'''
    def get_plot(self):
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}], [{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": True}]])
        marker_colors = np.full(self.data.volume.shape, np.nan, dtype=object)
        marker_colors[self.data.volume > self.data.volume.shift()] = 'green'
        marker_colors[self.data.volume == self.data.volume.shift()] = 'grey'
        marker_colors[self.data.volume < self.data.volume.shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.volume, x=self.data.index, name="Volume", marker_color=marker_colors), row=1, col=1)

        fig.add_trace(go.Candlestick(x=self.data.index, open=self.data.open, high=self.data.high, low=self.data.low, close=self.data.close, name=self.pair), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.bband_upper, x=self.data.index, mode='lines', line_shape='spline', name='bband_upper', line=dict(color='magenta')), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.bband_middle, x=self.data.index, mode='lines', line_shape='spline', name='bband_middle', line=dict(color='magenta')), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.bband_lower, x=self.data.index, mode='lines', line_shape='spline', name='bband_lower', line=dict(color='magenta')), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.bought, x=self.data.index, name='bought', mode='markers', marker=dict(color='cyan', symbol='circle-open', size=10)), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.sold, x=self.data.index, name='sold', mode='markers', marker=dict(color='yellow', symbol='circle-open', size=10)), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.stoped_loss, x=self.data.index, name='stoped_loss', mode='markers',
                      marker=dict(color='magenta', symbol='circle-open', size=10)), row=1, col=1, secondary_y=True)

        fig.add_trace(go.Scatter(y=self.data.mfi, x=self.data.index, mode='lines', line_shape='spline', name="Money Flow Index", marker_color='orange'), row=2, col=1)
        fig.add_trace(go.Scatter(y=self.data.rsi, x=self.data.index, mode='lines', line_shape='spline', name="RSI", marker_color='purple'), row=2, col=1, secondary_y=True)

        marker_colors = np.full(self.data['ao'].shape, np.nan, dtype=object)
        marker_colors[self.data['ao'] >= self.data['ao'].shift()] = 'green'
        marker_colors[self.data['ao'] < self.data['ao'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.ao, x=self.data.index, name="awesome oscillator", marker_color=marker_colors), row=3, col=1)

        marker_colors[self.data['profit_diff'] > self.data['profit_diff'].shift()] = 'green'
        marker_colors[self.data['profit_diff'] == self.data['profit_diff'].shift()] = 'grey'
        marker_colors[self.data['profit_diff'] < self.data['profit_diff'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.profit_diff, x=self.data.index, name="profit_diff", marker_color=marker_colors), row=4, col=1)

        fig.add_trace(go.Scatter(y=self.data.hodl_profit, x=self.data.index, mode='lines', line_shape='spline', name='hodl_profit', line=dict(color='yellow')), row=4, col=1, secondary_y=True)
        if 'old_trade_profit' in self.data.columns:
            fig.add_trace(go.Scatter(y=self.data.old_trade_profit, x=self.data.index, mode='lines', line_shape='spline',
                          name='trade_profit (old)', line=dict(color='lime')), row=4, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.trade_profit, x=self.data.index, mode='lines', line_shape='spline', name='trade_profit (new)', line=dict(color='green')), row=4, col=1, secondary_y=True)

        fig.update_xaxes(rangeslider_visible=False, spikemode='across', spikesnap='cursor', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_layout(template="plotly_dark", hovermode='x', spikedistance=-1)
        fig.update_traces(xaxis='x')
        return fig
        '''
