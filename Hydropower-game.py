import sys
import time
import numpy as np
from PyQt5.QtWidgets import QPushButton, QMessageBox, QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from ortools.math_opt.python import mathopt

matplotlib.use('Qt5Agg')
# Set the global font size
plt.rcParams['font.size'] = 15

N_timesteps = 24
hours = np.arange(N_timesteps)
TARGET = 16  # Daily release value
min_release = 0.2
max_ramp_up = 0.2
max_ramp_down = 0.3
target_tol = 0.1
price_values = 0.02*np.array([20,18,17,16,18,25,30,35,32,30,28,27,28,30,32,35,40,45,42,38,35,30,25,22])

# build optimization model
model = mathopt.Model(name="game")
release = [model.add_variable(lb=0.0) for h in hours]
model.maximize(sum([release[h]*price_values[h] for h in hours]))
model.add_linear_constraint(sum([release[h] for h in hours]) == TARGET)
for h in hours:
    model.add_linear_constraint(release[h] >= min_release)
    model.add_linear_constraint(release[h] - release[h-1] <= max_ramp_up)
    model.add_linear_constraint(release[h] - release[h-1] >= -max_ramp_down)

params = mathopt.SolveParameters(enable_output=False)
result = mathopt.solve(model, mathopt.SolverType.GLOP, params=params)

optimal_value = 0
if result.termination.reason == mathopt.TerminationReason.OPTIMAL:
    optimal_value = result.objective_value()
    

class BarGraphCanvas(FigureCanvas):
    def __init__(self, parent=None, on_update_callback=None):
        self.fig, self.ax = Figure(figsize=(25, 8), dpi=100), None
        super(BarGraphCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.on_update_callback = on_update_callback  # Callback for updating total sum
        
        self.y_values = 0.5*np.ones(N_timesteps)
        
        self.start_time = time.time()
        
        self.ax = self.fig.add_subplot(111)
        self.bars = self.ax.bar(hours, self.y_values, color='#1f77b4')
        self.price_line = self.ax.plot(price_values, color='k')
        
        self.total_revenue = sum(self.y_values*price_values)
        
        # self.ax.set_ylabel('Hourly release (AF/hr)')
        # self.ax.set_xlabel('Hours')
        self.selected_bar = None
        self.y_value_texts = []
        
        self.mpl_connect('button_press_event', self.on_click)
        self.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.mpl_connect('button_release_event', self.on_release)
        
        self.update_chart()
        self.fig.tight_layout()

    def update_chart(self, from_pick=True):
        self.ax.clear()
        self.ax.set_ylabel('Hourly release (AF/hr)')
        self.ax.set_xlabel('Hours')
        if from_pick:
            self.y_values = np.array([bar.get_height() for bar in self.bars])
        # print(sum(self.y_values))
        # self.bars = self.ax.bar(np.arange(10), [bar.get_height() for bar in self.bars], color='blue')
        self.bars = self.ax.bar(hours, self.y_values, color='#1f77b4', label='Releases (AF)')
        self.price_line = self.ax.plot(price_values, color='k', label='Price ($/AF)')
        self.y_value_texts = [self.ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{bar.get_height():.2f}', 
                                          ha='center', va='bottom') for bar in self.bars]
        self.ax.legend()
        self.ax.set_ylim(0, 2.5)
        self.draw()
        
        if self.on_update_callback:
            # total_sum = sum(bar.get_height() for bar in self.bars)
            self.total_sum = sum(self.y_values)
            self.total_revenue = sum(self.y_values*price_values)
            self.minimum_release_rate = np.min(self.y_values)
            self.ramp_rate = np.roll(self.y_values, -1) - self.y_values
            self.maximum_ramp_up_rate = np.max(self.ramp_rate)
            self.maximum_ramp_down_rate = np.max(-self.ramp_rate)
            self.on_update_callback(self.total_sum, self.total_revenue, self.minimum_release_rate, self.maximum_ramp_up_rate, self.maximum_ramp_down_rate)  # Trigger callback to update sum bar
            # self.on_update_callback(total_revenue)  # Trigger callback to update revenue bar
            self.feasible_minimum_release_rate = (self.minimum_release_rate >= min_release - 0.1*target_tol).all()
            self.feasible_maximum_ramp_up_rate = (self.maximum_ramp_up_rate <= max_ramp_up + 0.1*target_tol).all()
            self.feasible_maximum_ramp_down_rate = (self.maximum_ramp_down_rate <= max_ramp_down + 0.1*target_tol).all()
            self.feasible_total_sum = (self.total_sum - TARGET <= target_tol) & (self.total_sum - TARGET >= -target_tol)
            self.feasible_solution = self.feasible_minimum_release_rate & self.feasible_maximum_ramp_up_rate & self.feasible_maximum_ramp_down_rate & self.feasible_total_sum
    
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        for i, bar in enumerate(self.bars):
            contains, _ = bar.contains(event)
            if contains:
                self.selected_bar = i
                break
    
    def on_mouse_move(self, event):
        if self.selected_bar is None or event.inaxes != self.ax:
            return
        
        bar = self.bars[self.selected_bar]
        new_height = max(min(event.ydata, 1.5), 0)  # Constrain the height between 0 and 1.5
        bar.set_height(new_height)
        
        # Update the text on top of the bar with the new value
        self.y_value_texts[self.selected_bar].set_y(new_height)
        self.y_value_texts[self.selected_bar].set_text(f'{new_height:.2f}')
        self.update_chart()
    
    def on_release(self, event):
        self.selected_bar = None  # Release the bar

class TotalBarCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig, self.ax = Figure(figsize=(4, 6), dpi=100), None
        super(TotalBarCanvas, self).__init__(fig)
        self.setParent(parent)
        self.ax = fig.add_subplot(111)
        self.total_bar = None
        self.target_text = None
        # self.target_value = target_value
        # self.title = title
        # self.ax.set_title('XXX')
        self.draw_total_bar(0, 'XXX', 1, 'XXX', 'eq')
    
    def draw_total_bar(self, total, title, target_value, target_name, cst_direction):
        self.ax.clear()
        self.ax.set_title(title)
        self.total_bar = self.ax.bar([0], [total], color='#1f77b4')
        self.ax.set_ylim(0, target_value*1.5)  # Set a suitable limit for the total sum
        self.ax.axhline(y=target_value, color='black', linestyle='--')  # Black target line
        self.ax.text(0.0, target_value, target_name, ha='center', va='bottom', color='k')
        
        if cst_direction=='eq':
            if abs(total - target_value) <= target_tol:
                self.total_bar[0].set_color('tab:green')
        elif cst_direction=='geq':
            if total >= target_value - 0.1*target_tol:
                self.total_bar[0].set_color('tab:green')
        elif cst_direction=='leq':
            if total <= target_value + 0.1*target_tol:
                self.total_bar[0].set_color('tab:green')            
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.draw()
        

class BarGraphWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Hydropower game")
        
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)  # Vertical layout to hold everything
        
        graphs_layout = QHBoxLayout()  # Horizontal layout for the hourly graph and the revenue
        
        rules_layout = QHBoxLayout()   # Horizontal layout for the rules
        
        buttons_layout = QHBoxLayout()   # Horizontal layout for the buttons

        # layout = QHBoxLayout(self.central_widget)
        
        self.game_instructions = QLabel("""Instructions:
Find the best hydropower revenue by changing the hourly releases.
You must make sure that all envrionmental rules are respected:
Daily release targte, minimum release rate,
maximum ramp up and maximum ramp down""", self.central_widget)
        main_layout.addWidget(self.game_instructions)
        
        # Create an "Initialize" button at the top
        self.initialize_button = QPushButton("Start", self.central_widget)
        self.initialize_button.clicked.connect(self.initialize_action)  # Connect to an action
        # Create an "Optimize" button at the top
        self.optimize_button = QPushButton("Optimize", self.central_widget)
        self.optimize_button.clicked.connect(self.optimize_action)  # Connect to an action
        # Create a "Check" button
        self.check_button = QPushButton("Check solution", self.central_widget)
        self.check_button.clicked.connect(self.check_action)  # Connect to an action
        buttons_layout.addWidget(self.initialize_button)
        buttons_layout.addWidget(self.check_button)
        buttons_layout.addWidget(self.optimize_button)
        
        main_layout.addLayout(buttons_layout)
        
        self.total_bar_graph = TotalBarCanvas(self.central_widget)  # Initialize total_bar_graph first
        self.revenue_bar_graph = TotalBarCanvas(self.central_widget)  # Initialize revenue_bar_graph first    
        self.minimum_release_bar_graph = TotalBarCanvas(self.central_widget)  # Initialize revenue_bar_graph first    
        self.max_ramp_up_bar_graph = TotalBarCanvas(self.central_widget)  # Initialize revenue_bar_graph first    
        self.max_ramp_down_bar_graph = TotalBarCanvas(self.central_widget)  # Initialize revenue_bar_graph first    
        self.bar_graph = BarGraphCanvas(self.central_widget, self.update_total_bar)  # Assign the callback
                
        graphs_layout.addWidget(self.bar_graph)
        rules_layout.addWidget(self.revenue_bar_graph)
        rules_layout.addWidget(self.total_bar_graph)
        rules_layout.addWidget(self.minimum_release_bar_graph)
        rules_layout.addWidget(self.max_ramp_up_bar_graph)
        rules_layout.addWidget(self.max_ramp_down_bar_graph)
    
        ## Create a QLabel for the GIF and set the QMovie
        # self.gif_label = QLabel(self.central_widget)
        # self.gif_movie = QMovie(r"C:\Users\quent\Documents\Argonne\GitHub\Hydropower_game\ezgif-3-ab8f1922df.gif")  # Path to your animated GIF
        # self.gif_label.setMovie(self.gif_movie)
        # graphs_layout.addWidget(self.gif_label)
        
        main_layout.addLayout(graphs_layout)
        main_layout.addLayout(rules_layout)

        # Create a QLabel to display credit text and add it to the main layout
        self.credit_label = QLabel("""A WPTO-funded ANL-NREL outreach project:
Quentin Ploussard, Elise DeGeorge, Cathy Milostan, 
Jonghwan Kwon 'JK', Matt Mahalik, Tom Veselka, Bree Mendlin""", self.central_widget)
        self.credit_label.setAlignment(Qt.AlignLeft)  # Align text to the left
        main_layout.addWidget(self.credit_label)
    
        # Start the animated GIF
        # self.gif_movie.start()
    
    def update_total_bar(self, total_sum, total_revenue, minimum_release_rate, maximum_ramp_up_rate, maximum_ramp_down_rate):
        self.total_bar_graph.draw_total_bar(total_sum, 'Total release (AF)', TARGET, 'Daily target', 'eq')
        self.revenue_bar_graph.draw_total_bar(total_revenue, 'Total revenue ($)', optimal_value, 'Optimal value', 'eq')
        self.minimum_release_bar_graph.draw_total_bar(minimum_release_rate, 'Minimum release (AF/hr)', min_release, 'Minimum rate', 'geq')
        self.max_ramp_up_bar_graph.draw_total_bar(maximum_ramp_up_rate, 'Maximum ramp up', max_ramp_up, 'Ramp up limit', 'leq')
        self.max_ramp_down_bar_graph.draw_total_bar(maximum_ramp_down_rate, 'Maximum ramp down', max_ramp_down, 'Ramp down limit', 'leq')

    def initialize_action(self):
        self.bar_graph.y_values = 0.5*np.ones(N_timesteps)
        self.bar_graph.update_chart(from_pick=False)
        self.bar_graph.start_time = time.time()
        # self.total_bar_graph.y_values = np.array([result.variable_values()[release[h]] for h in hours])

    def check_action(self):
        optimal_value = result.objective_value()
        percent_solution = 100*self.bar_graph.total_revenue/optimal_value
        time_to_find = time.time() - self.bar_graph.start_time
        feasibility_text = "The solution is not feasible, try again...\n"
        percent_solution_text = ""
        time_to_find_text = ""
        if self.bar_graph.feasible_solution:
            feasibility_text = "The solution is feasible, great!\n"
            percent_solution_text = f"You are {percent_solution:.0f}% close to the optimal solution!\n"
            time_to_find_text = f"Time to find: {time_to_find:.0f}s"
        self.bar_graph.start_time = time.time()
        self.show_message(feasibility_text+percent_solution_text+time_to_find_text)

    def optimize_action(self):
        self.bar_graph.start_time = time.time()
        if result.termination.reason == mathopt.TerminationReason.OPTIMAL:
            optimal_value = result.objective_value()
            self.bar_graph.y_values = np.array([result.variable_values()[release[h]] for h in hours])
            self.bar_graph.update_chart(from_pick=False)
            # self.total_bar_graph.y_values = np.array([result.variable_values()[release[h]] for h in hours])
            self.show_message(f"The optimal solution is {optimal_value:.2f}")
        else:
            self.show_message("The model was infeasible.")
            
    def show_message(self, message):
        # Create a message box for displaying the result
        msg = QMessageBox()
        msg.setWindowTitle("Result")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        # msg.buttonClicked.connect(self.close)  # Close the app after the user clicks "OK"
        msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BarGraphWindow()
    window.show()
    window.move(0, 0) 
    sys.exit(app.exec_())
