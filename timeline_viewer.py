import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import re
import time
import threading
from typing import List, Tuple

class TimelineViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("技能时间轴查看器")
        self.root.geometry("1200x650")
        self.root.configure(bg="#2b2b2b")

        self.timeline_data = []

        # 蛇胆使用记录系统
        self.serpent_uses = []  # 记录蛇胆使用的时间点，格式：[(使用时间, 技能名称)]
        self.max_serpent_offerings = 3  # 最大蛇胆数量
        self.serpent_regen_interval = 30.0  # 30秒回复一个蛇胆

        self.serpent_displays = []  # 存储所有蛇胆显示组件的引用

        # 蛇胆显示相关
        self.serpent_history_label = None

        self.setup_ui()

    def setup_ui(self):
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg="#404040", height=50)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # 加载文件按钮
        load_btn = tk.Button(
            toolbar, 
            text="加载文件", 
            command=self.load_file,
            bg="#4CAF50",
            fg="white",
            font=("黑体", 12, "bold"),
            padx=20,
            pady=5
        )
        load_btn.pack(side=tk.LEFT, padx=5)

        # 文件路径标签
        self.file_label = tk.Label(
            toolbar,
            text="未选择文件",
            bg="#404040",
            fg="#cccccc",
            font=("黑体", 10)
        )
        self.file_label.pack(side=tk.LEFT, padx=20)

        # 蛇胆控制面板
        control_frame = tk.Frame(self.root, bg="#333333", height=60)
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        control_frame.pack_propagate(False)

        # 重置蛇胆按钮
        reset_btn = tk.Button(
            control_frame,
            text="🔄 重置蛇胆",
            command=self.reset_serpent,
            bg="#FF5722",
            fg="white",
            font=("黑体", 12, "bold"),
            width=10,
            height=1
        )
        reset_btn.pack(side=tk.LEFT, padx=15, pady=15)

        # 蛇胆使用历史显示
        self.serpent_history_label = tk.Label(
            control_frame,
            text="蛇胆使用记录: 无",
            bg="#333333",
            fg="#E1BEE7",
            font=("黑体", 11)
        )
        self.serpent_history_label.pack(side=tk.LEFT, padx=20, pady=15)

        # 全局蛇胆回复状态
        self.global_progress_label = tk.Label(
            control_frame,
            text="",
            bg="#333333",
            fg="#4CAF50",
            font=("黑体", 10, "bold")
        )
        self.global_progress_label.pack(side=tk.RIGHT, padx=20, pady=15)

        # 主要内容区域
        main_frame = tk.Frame(self.root, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 时间轴框架
        self.timeline_frame = tk.Frame(main_frame, bg="#363636")
        self.timeline_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 滚动条
        scrollbar = tk.Scrollbar(self.timeline_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建Canvas用于滚动
        self.canvas = tk.Canvas(
            self.timeline_frame, 
            bg="#363636",
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)

        # 内部框架用于放置时间轴项目
        self.inner_frame = tk.Frame(self.canvas, bg="#363636")
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 初始提示
        self.show_initial_message()

    def show_initial_message(self):
        """显示初始提示信息"""
        message_frame = tk.Frame(self.inner_frame, bg="#363636", pady=50)
        message_frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(
            message_frame,
            text="技能时间轴查看器",
            font=("黑体", 20, "bold"),
            fg="#4CAF50",
            bg="#363636"
        )
        title_label.pack(pady=10)

        subtitle_label = tk.Label(
            message_frame,
            text="点击'加载文件'按钮选择M1S格式的文本文件",
            font=("黑体", 12),
            fg="#cccccc",
            bg="#363636"
        )
        subtitle_label.pack(pady=5)

        format_label = tk.Label(
            message_frame,
            text="支持格式: 时间 \"技能名称\" (例如: 7.9 \"--中间--\")",
            font=("黑体", 10),
            fg="#888888",
            bg="#363636"
        )
        format_label.pack(pady=20)

    def load_file(self):
        """加载文件"""
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                self.parse_file(file_path)
                self.file_label.config(text=f"已加载: {file_path.split('/')[-1]}")
                self.display_timeline()
            except Exception as e:
                messagebox.showerror("错误", f"加载文件失败：{str(e)}")

    def parse_file(self, file_path: str):
        """解析文件内容"""
        self.timeline_data = []

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # 正则表达式匹配时间和技能名称
        # 匹配格式：时间 "技能名称" 或 时间 技能名称（不带引号）
        pattern = r'^(\d+\.?\d*)\s+"([^"]+)"'
        pattern_no_quotes = r'^(\d+\.?\d*)\s+([^"#\s][^#]*?)(?:\s+[A-Z]|$)'

        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('hideall'):
                continue

            # 先尝试匹配带引号的格式
            match = re.match(pattern, line)
            if match:
                time_str = match.group(1)
                skill_name = match.group(2)
                self.timeline_data.append((float(time_str), skill_name))
                continue

            # 再尝试匹配不带引号的格式
            match = re.match(pattern_no_quotes, line)
            if match:
                time_str = match.group(1)
                skill_name = match.group(2).strip()
                if skill_name and not skill_name.startswith('label') and not skill_name.startswith('--'):
                    self.timeline_data.append((float(time_str), skill_name))

        # 按时间排序
        self.timeline_data.sort(key=lambda x: x[0])

    def display_timeline(self):
        """显示时间轴"""
        # 清除旧内容
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        # 重置蛇胆显示列表
        self.serpent_displays = []

        if not self.timeline_data:
            self.show_no_data_message()
            return

        # 标题栏
        header_frame = tk.Frame(self.inner_frame, bg="#404040", height=40)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        time_header = tk.Label(
            header_frame,
            text="时间",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#404040",
            width=10
        )
        time_header.pack(side=tk.LEFT, padx=(20, 0), pady=10)

        skill_header = tk.Label(
            header_frame,
            text="技能名称",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#404040"
        )
        skill_header.pack(side=tk.LEFT, padx=(50, 0), pady=10)

        button_header = tk.Label(
            header_frame,
            text="操作/偏移",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#404040"
        )
        button_header.pack(side=tk.LEFT, padx=(20, 0), pady=10)

        serpent_header = tk.Label(
            header_frame,
            text="蛇胆量谱",
            font=("Arial", 14, "bold"),
            fg="#E1BEE7",
            bg="#404040"
        )
        serpent_header.pack(side=tk.RIGHT, padx=(0, 30), pady=10)

        # 时间轴项目
        for i, (time_val, skill_name) in enumerate(self.timeline_data):
            self.create_timeline_item(i, time_val, skill_name)

    def create_timeline_item(self, index: int, time_val: float, skill_name: str):
        """创建时间轴项目"""
        # 交替背景色
        bg_color = "#2e2e2e" if index % 2 == 0 else "#323232"

        # 特殊技能的颜色标记
        if "--" in skill_name:
            accent_color = "#FFA726"  # 橙色用于特殊标记
        elif any(keyword in skill_name for keyword in ["连指向", "定格"]):
            accent_color = "#EF5350"  # 红色用于攻击技能
        elif any(keyword in skill_name for keyword in ["场地", "热舞"]):
            accent_color = "#42A5F5"  # 蓝色用于场地技能
        elif any(keyword in skill_name for keyword in ["同步", "Reset"]):
            accent_color = "#66BB6A"  # 绿色用于同步技能
        else:
            accent_color = "#AB47BC"  # 紫色用于其他技能

        item_frame = tk.Frame(self.inner_frame, bg=bg_color, height=55)
        item_frame.pack(fill=tk.X, pady=1)
        item_frame.pack_propagate(False)

        # 时间显示
        time_label = tk.Label(
            item_frame,
            text=f"{time_val:.1f}s",
            font=("Arial", 11, "bold"),
            fg="#FFD54F",
            bg=bg_color,
            width=8,
            anchor="w"
        )
        time_label.pack(side=tk.LEFT, padx=(20, 5), pady=15)

        # 连接线
        line_frame = tk.Frame(item_frame, bg=accent_color, width=3, height=40)
        line_frame.pack(side=tk.LEFT, padx=(5, 15), pady=5)
        line_frame.pack_propagate(False)

        # 技能名称（简化显示，不使用框架包装）
        skill_label = tk.Label(
            item_frame,
            text=skill_name,
            font=("Arial", 11),
            fg="white",
            bg=bg_color,
            anchor="w"
        )
        skill_label.pack(side=tk.LEFT, pady=15, padx=(0, 15))

        # 操作区域框架（包含按钮和偏移时间）
        action_frame = tk.Frame(item_frame, bg=bg_color)
        action_frame.pack(side=tk.LEFT, pady=10, padx=(10, 0))

        # 技能按钮
        # 创建独立的偏移时间变量
        offset_var = tk.StringVar(value="0")

        skill_button = tk.Button(
            action_frame,
            text="释放",
            font=("黑体", 9, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            relief="raised",
            bd=2,
            width=6,
            height=1,
            command=lambda t=time_val, s=skill_name, offset=offset_var: self.use_serpent_offering_with_individual_offset(t, s, offset)
        )
        skill_button.pack(side=tk.LEFT)

        # 偏移时间输入框
        offset_label = tk.Label(
            action_frame,
            text="±",
            font=("黑体", 10),
            fg="#FFD54F",
            bg=bg_color,
            width=2
        )
        offset_label.pack(side=tk.LEFT, padx=(5, 2))

        offset_entry = tk.Entry(
            action_frame,
            textvariable=offset_var,
            width=4,
            font=("黑体", 10),
            bg="#555555",
            fg="white",
            justify="center"
        )
        offset_entry.pack(side=tk.LEFT)

        offset_unit = tk.Label(
            action_frame,
            text="s",
            font=("黑体", 10),
            fg="#FFD54F",
            bg=bg_color,
            width=1
        )
        offset_unit.pack(side=tk.LEFT, padx=(2, 0))

        # 蛇胆量谱显示区域
        serpent_frame = tk.Frame(item_frame, bg=bg_color, width=150, height=50)
        serpent_frame.pack(side=tk.RIGHT, padx=(0, 20), pady=0)
        serpent_frame.pack_propagate(False)

        # 创建蛇胆显示
        serpent_display = self.create_serpent_display(serpent_frame, bg_color, time_val)

        # 添加到蛇胆显示列表
        self.serpent_displays.append(serpent_display)

        # 添加悬停效果
        widgets_to_bind = [item_frame, time_label, skill_label, action_frame, skill_button, offset_label, offset_entry, offset_unit, serpent_frame]

        def on_enter(event, frame=item_frame, orig_color=bg_color, widgets=widgets_to_bind):
            hover_color = "#404040"
            frame.config(bg=hover_color)
            for widget in widgets:
                if isinstance(widget, (tk.Label, tk.Frame)) and widget != offset_entry:
                    try:
                        widget.config(bg=hover_color)
                    except:
                        pass

        def on_leave(event, frame=item_frame, orig_color=bg_color, widgets=widgets_to_bind):
            frame.config(bg=orig_color)
            for widget in widgets:
                if isinstance(widget, (tk.Label, tk.Frame)) and widget != offset_entry:
                    try:
                        widget.config(bg=orig_color)
                    except:
                        pass

        for widget in widgets_to_bind:
            if widget != offset_entry:  # 不绑定输入框，避免影响输入
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

    def create_serpent_display(self, parent_frame, bg_color, time_val):
        """创建蛇胆量谱显示"""
        # 蛇胆标题
        title_label = tk.Label(
            parent_frame,
            text="蛇胆:",
            font=("Arial", 8, "bold"),
            fg="#E1BEE7",
            bg=bg_color
        )
        title_label.place(x=2, y=2)

        # 蛇胆图标容器
        serpent_icons = []
        for i in range(3):
            x_pos = 30 + i * 25

            # 蛇胆背景框
            bg_frame = tk.Frame(
                parent_frame,
                bg="#1a1a2e",
                width=20,
                height=16,
                relief="sunken",
                bd=1
            )
            bg_frame.place(x=x_pos, y=5)
            bg_frame.pack_propagate(False)

            # 蛇胆图标
            serpent_icon = tk.Label(
                bg_frame,
                text="◆",
                font=("Arial", 10, "bold"),
                fg="#9C27B0",
                bg="#1a1a2e"
            )
            serpent_icon.pack(expand=True)

            serpent_icons.append((bg_frame, serpent_icon))

        # 数量显示
        count_label = tk.Label(
            parent_frame,
            text="",
            font=("Arial", 8, "bold"),
            fg="#FFD54F",
            bg=bg_color
        )
        count_label.place(x=105, y=6)

        # 回复进度条背景
        progress_bg = tk.Frame(
            parent_frame,
            bg="#1a1a2e",
            width=106,
            height=8,
            relief="sunken",
            bd=1
        )
        progress_bg.place(x=30, y=25)
        progress_bg.pack_propagate(False)

        # 回复进度条
        progress_bar = tk.Frame(
            progress_bg,
            bg="#4CAF50",
            height=6
        )

        # 进度条文字
        progress_label = tk.Label(
            parent_frame,
            text="",
            font=("Arial", 7),
            fg="#888888",
            bg=bg_color
        )
        progress_label.place(x=2, y=35)

        def update_display():
            """更新蛇胆显示状态"""
            # 计算当前时间点的蛇胆数量
            serpent_count = self.calculate_serpent_at_time(time_val)

            for i, (bg_frame, icon) in enumerate(serpent_icons):
                if i < serpent_count:
                    # 有蛇胆 - 亮紫色
                    icon.config(fg="#E1BEE7", text="◆")
                    bg_frame.config(bg="#2d1b69")
                else:
                    # 无蛇胆 - 暗灰色
                    icon.config(fg="#555555", text="◇")
                    bg_frame.config(bg="#1a1a2e")

            count_label.config(text=f"{serpent_count}/3")

            # 更新进度条
            self.update_serpent_progress_bar(time_val, progress_bar, progress_label, serpent_count)

        # 初始显示
        update_display()

        return update_display

    def show_no_data_message(self):
        """显示无数据消息"""
        message_frame = tk.Frame(self.inner_frame, bg="#363636", pady=50)
        message_frame.pack(fill=tk.BOTH, expand=True)

        message_label = tk.Label(
            message_frame,
            text="未找到有效的时间轴数据",
            font=("黑体", 16),
            fg="#ff6b6b",
            bg="#363636"
        )
        message_label.pack(pady=20)

        help_label = tk.Label(
            message_frame,
            text="请确认文件格式正确：\n时间 \"技能名称\" (例如: 7.9 \"--中间--\")",
            font=("黑体", 12),
            fg="#888888",
            bg="#363636",
            justify=tk.CENTER
        )
        help_label.pack(pady=10)

    def _on_mousewheel(self, event):
        """处理鼠标滚轮滚动"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_frame_configure(self, event):
        """当内部框架大小改变时更新滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """当画布大小改变时调整内部框架宽度"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def reset_serpent(self):
        """重置蛇胆使用记录"""
        self.serpent_uses = []
        self.update_serpent_history_display()
        self.update_all_serpent_displays()

    def calculate_serpent_at_time(self, target_time: float) -> int:
        """计算指定时间点的蛇胆数量（优化版本）"""
        # 开始时有3个蛇胆
        current_serpent = 3

        if not self.serpent_uses:
            return current_serpent

        # 获取相关使用记录（优化：减少不必要的计算）
        relevant_uses = [(use_time, skill_name) for use_time, skill_name in self.serpent_uses if use_time <= target_time]
        if not relevant_uses:
            return current_serpent

        relevant_uses.sort(key=lambda x: x[0])  # 按时间排序

        # 跟踪使用和回复事件
        events = []
        for use_time, skill_name in relevant_uses:
            events.append((use_time, -1))  # 使用蛇胆事件
            recovery_time = use_time + self.serpent_regen_interval
            if recovery_time <= target_time:
                events.append((recovery_time, 1))  # 回复蛇胆事件

        # 按时间顺序处理事件
        events.sort()
        for event_time, change in events:
            current_serpent = max(0, min(self.max_serpent_offerings, current_serpent + change))

        return current_serpent

    def get_next_serpent_recovery_info(self, target_time: float) -> tuple:
        """获取下一个蛇胆回复信息（优化版本）"""
        if not self.serpent_uses:
            return None, 0.0, 0.0

        # 直接寻找最近的未回复使用记录
        next_recovery = None
        min_recovery_time = float('inf')

        for use_time, skill_name in self.serpent_uses:
            recovery_time = use_time + self.serpent_regen_interval
            if recovery_time > target_time and recovery_time < min_recovery_time:
                min_recovery_time = recovery_time
                next_recovery = (use_time, skill_name, recovery_time)

        if next_recovery is None:
            return None, 0.0, 0.0

        use_time, skill_name, recovery_time = next_recovery

        # 快速计算进度
        elapsed = target_time - use_time
        progress = max(0.0, min(1.0, elapsed / self.serpent_regen_interval))

        return skill_name, progress, recovery_time - target_time

    def update_serpent_progress_bar(self, time_val: float, progress_bar: tk.Frame, progress_label: tk.Label, serpent_count: int):
        """更新蛇胆回复进度条"""
        if serpent_count >= self.max_serpent_offerings:
            # 蛇胆已满，隐藏进度条
            progress_bar.place_forget()
            progress_label.config(text="已满")
            return

        # 获取下一个回复信息
        next_skill, progress, time_remaining = self.get_next_serpent_recovery_info(time_val)

        if next_skill is None:
            # 没有待回复的蛇胆
            progress_bar.place_forget()
            progress_label.config(text="待使用")
            return

        # 显示进度条
        progress_width = int(104 * progress)  # 104是进度条背景宽度减去边框
        progress_bar.config(width=max(1, progress_width))
        progress_bar.place(x=1, y=1)

        # 根据进度改变颜色
        if progress < 0.3:
            color = "#FF5722"  # 红色 - 刚开始
        elif progress < 0.7:
            color = "#FF9800"  # 橙色 - 进行中
        else:
            color = "#4CAF50"  # 绿色 - 即将完成

        progress_bar.config(bg=color)

        # 更新文字显示
        if time_remaining > 0:
            progress_label.config(text=f"回复中: {time_remaining:.1f}s")
        else:
            progress_label.config(text="即将回复")

    def update_serpent_history_display(self):
        """更新蛇胆使用历史显示（优化版本）"""
        if not self.serpent_uses:
            self.serpent_history_label.config(text="蛇胆使用记录: 无")
            return

        # 优化：只构建一次字符串
        recent_uses = self.serpent_uses[-3:]  # 减少显示数量提高性能
        history_parts = [f"{use_time:.1f}s({skill_name[:2]})" for use_time, skill_name in recent_uses]
        history_text = "蛇胆使用记录: " + " ".join(history_parts)

        if len(self.serpent_uses) > 3:
            history_text += "..."

        self.serpent_history_label.config(text=history_text)

    def update_all_serpent_displays(self):
        """更新所有蛇胆显示"""
        for display_func in self.serpent_displays:
            if display_func:
                display_func()

    def quick_update_displays(self):
        """快速更新显示（优化版本）"""
        # 批量更新，减少UI重绘次数
        self.root.update_idletasks()

        # 只更新必要的组件
        self.update_serpent_history_display()

        # 延迟更新所有蛇胆显示以避免卡顿
        self.root.after_idle(self.update_all_serpent_displays)

    def update_status_message(self, message: str, color: str):
        """更新状态消息"""
        if hasattr(self, 'global_progress_label'):
            self.global_progress_label.config(text=message, fg=color)
            # 3秒后清除消息
            self.root.after(3000, lambda: self.clear_status_message())

    def clear_status_message(self):
        """清除状态消息"""
        if hasattr(self, 'global_progress_label'):
            # 恢复原来的全局进度显示
            if not self.serpent_uses:
                self.global_progress_label.config(text="", fg="#4CAF50")
            else:
                current_total_serpent = 3 - len([use for use in self.serpent_uses])
                if current_total_serpent < self.max_serpent_offerings:
                    self.global_progress_label.config(text="⏳ 蛇胆回复中...", fg="#4CAF50")
                else:
                    self.global_progress_label.config(text="✓ 蛇胆已满", fg="#4CAF50")

    def use_serpent_offering_with_individual_offset(self, base_time_val: float, skill_name: str, offset_var: tk.StringVar):
        """使用带独立偏移时间的蛇胆"""
        try:
            offset = float(offset_var.get())
        except (ValueError, AttributeError):
            offset = 0.0

        actual_time = base_time_val + offset

        # 确保时间不为负数
        if actual_time < 0:
            actual_time = 0.0

        # 计算实际使用时间点的蛇胆数量
        current_serpent = self.calculate_serpent_at_time(actual_time)

        if current_serpent > 0:
            # 记录使用（使用实际时间）
            self.serpent_uses.append((actual_time, skill_name))
            self.serpent_uses.sort()  # 保持时间顺序

            # 快速更新显示
            self.quick_update_displays()

            # 更新状态栏显示成功
            self.update_status_message(f"✓ 已使用蛇胆释放 {skill_name[:8]}... (时间: {actual_time:.1f}s)", "#4CAF50")
            return True
        else:
            # 更新状态栏显示失败
            self.update_status_message(f"✗ 蛇胆不足，无法释放 {skill_name[:8]}... (时间: {actual_time:.1f}s)", "#ff6b6b")
            return False

    def use_serpent_offering_with_offset(self, base_time_val: float, skill_name: str):
        """使用带时间偏移量的蛇胆（兼容性方法）"""
        return self.use_serpent_offering_with_individual_offset(base_time_val, skill_name, tk.StringVar(value="0"))

    def use_serpent_offering(self, time_val: float, skill_name: str):
        """使用一个蛇胆（无偏移量版本，保持兼容性）"""
        return self.use_serpent_offering_with_offset(time_val, skill_name)

    # 所有弹窗反馈方法已移除，使用状态栏显示代替

    def run(self):
        """运行应用程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TimelineViewer()
    app.run()
