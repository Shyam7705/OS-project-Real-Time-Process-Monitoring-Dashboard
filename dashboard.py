import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import psutil
import pandas as pd
from datetime import datetime
from data_collection import ProcessDataCollector
from data_processing import process_data, terminate_process, get_process_details

class ProcessMonitorDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Process Monitoring Dashboard")
        self.root.geometry("1200x700")
        self.root.configure(bg="#121212")

        # Style configuration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Helvetica", 10, "bold"), background="#0288D1", foreground="white")
        style.map("TButton", background=[("active", "#0277BD")])
        style.configure("Treeview", background="#1E1E1E", foreground="white", fieldbackground="#1E1E1E", font=("Helvetica", 10))
        style.configure("Treeview.Heading", background="#0288D1", foreground="white", font=("Helvetica", 11, "bold"))

        # Header
        header_frame = tk.Frame(root, bg="#0288D1")
        header_frame.pack(fill="x")
        header = tk.Label(header_frame, text="Real-Time Process Monitoring Dashboard", font=("Helvetica", 18, "bold"), bg="#0288D1", fg="white")
        header.pack(pady=10)

        # System summary
        summary_frame = tk.Frame(root, bg="#1E1E1E", highlightbackground="#0288D1", highlightthickness=2, relief="raised")
        summary_frame.pack(fill="x", padx=10, pady=5)
        self.cpu_label = tk.Label(summary_frame, text="Total CPU Usage: 0%", font=("Helvetica", 12, "bold"), bg="#1E1E1E", fg="#BBDEFB")
        self.cpu_label.pack(side="left", padx=20)
        self.memory_label = tk.Label(summary_frame, text="Total Memory Usage: 0 GB / 0 GB (0%)", font=("Helvetica", 12, "bold"), bg="#1E1E1E", fg="#BBDEFB")
        self.memory_label.pack(side="left", padx=20)

        # Search bar
        search_frame = tk.Frame(root, bg="#121212")
        search_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(search_frame, text="Search Process:", font=("Helvetica", 10, "bold"), bg="#121212", fg="#BBDEFB").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.debounce_search)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Helvetica", 10), bg="#1E1E1E", fg="white", insertbackground="white")
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(search_frame, text="Clear Search", command=self.clear_search).pack(side="left", padx=5)

        # Process table
        table_frame = tk.Frame(root, bg="#121212", highlightbackground="#0288D1", highlightthickness=2, relief="raised")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(table_frame, columns=('PID', 'Name', 'State', 'CPU (%)', 'Memory (MB)', 'Duration'), show='headings', height=10)
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.focus_set()
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        # Pagination controls
        pagination_frame = tk.Frame(root, bg="#121212")
        pagination_frame.pack(fill="x", padx=10, pady=5)
        self.page_var = tk.StringVar(value="Page 1")
        tk.Label(pagination_frame, textvariable=self.page_var, font=("Helvetica", 10), bg="#121212", fg="#BBDEFB").pack(side="left", padx=5)
        ttk.Button(pagination_frame, text="Previous", command=self.prev_page).pack(side="left", padx=5)
        ttk.Button(pagination_frame, text="Next", command=self.next_page).pack(side="left", padx=5)

        # Buttons
        button_frame = tk.Frame(root, bg="#121212")
        button_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(button_frame, text="Terminate Process", command=self.terminate_selected).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Show Details", command=self.show_details).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Refresh Now", command=self.refresh_now).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Deselect", command=self.deselect_process).pack(side="left", padx=5)  # Added from previous request

        # Graphs
        graph_frame = tk.Frame(root, bg="#121212", highlightbackground="#0288D1", highlightthickness=2, relief="raised")
        graph_frame.pack(fill="x", padx=10, pady=10)
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.fig.patch.set_facecolor("#1E1E1E")
        self.ax1.set_facecolor("#2E2E2E")
        self.ax2.set_facecolor("#2E2E2E")
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack()
        self.cpu_data = []
        self.memory_data = []

        # Status bar
        self.status_bar = tk.Label(root, text="Last Updated: Not yet updated", font=("Helvetica", 10), bg="#121212", fg="#BBDEFB", anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=5)

        # Initialize process data
        self.collector = ProcessDataCollector()
        self.all_processes = pd.DataFrame()
        self.filtered_processes = pd.DataFrame()
        self.search_after_id = None
        self.last_graph_update = 0
        self.current_page = 0
        self.processes_per_page = 50
        self.selected_pid = None

        # Start real-time updates
        self.running = True
        self.update_thread = threading.Thread(target=self.update_data_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            pid = self.tree.item(selected[0])['values'][0]
            self.selected_pid = pid
            print(f"Selected PID: {pid}")
        else:
            self.selected_pid = None
            print("No selection")

    def update_data_loop(self):
        while self.running:
            self.root.after(0, self.update_data_once)
            time.sleep(2)

    def update_data_once(self):
        try:
            self.status_bar.config(text="Updating data...")
            raw_data = self.collector.get_process_data()
            df = process_data(raw_data)

            # Update system summary
            total_cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            total_memory_percent = memory.percent
            used_memory_gb = memory.used / (1024 ** 3)  # Convert bytes to GB
            total_memory_gb = memory.total / (1024 ** 3)  # Convert bytes to GB
            self.cpu_label.config(text=f"Total CPU Usage: {total_cpu}%")
            self.memory_label.config(text=f"Total Memory Usage: {used_memory_gb:.2f} GB / {total_memory_gb:.2f} GB ({total_memory_percent}%)")

            # Preserve selection
            selected_pid = self.selected_pid
            self.all_processes = df

            # Apply search filter
            search_term = self.search_var.get().strip().lower()
            if search_term:
                self.filtered_processes = self.all_processes[self.all_processes['name'].str.lower().str.contains(search_term, na=False)]
            else:
                self.filtered_processes = self.all_processes

            # Update table
            self.update_table()

            # Restore selection
            if selected_pid:
                for item in self.tree.get_children():
                    if int(self.tree.item(item)['values'][0]) == selected_pid:
                        self.tree.selection_set(item)
                        self.selected_pid = selected_pid
                        break

            # Update graphs
            current_time = time.time()
            if current_time - self.last_graph_update >= 4:
                self.cpu_data.append(total_cpu)
                self.memory_data.append(total_memory_percent)  # Still using percentage for graph
                if len(self.cpu_data) > 60:
                    self.cpu_data.pop(0)
                    self.memory_data.pop(0)

                self.ax1.clear()
                self.ax1.plot(self.cpu_data, label="CPU Usage (%)", color="#0288D1", linewidth=2)
                self.ax1.set_title("CPU Usage Over Time", color="white", fontsize=12)
                self.ax1.set_ylim(0, 100)
                self.ax1.legend(facecolor="#2E2E2E", edgecolor="white", labelcolor="white")
                self.ax1.tick_params(colors="white")
                self.ax1.grid(True, color="gray", linestyle="--", alpha=0.5)

                self.ax2.clear()
                self.ax2.plot(self.memory_data, label="Memory Usage (%)", color="#FFCA28", linewidth=2)
                self.ax2.set_title("Memory Usage Over Time", color="white", fontsize=12)
                self.ax2.set_ylim(0, 100)
                self.ax2.legend(facecolor="#2E2E2E", edgecolor="white", labelcolor="white")
                self.ax2.tick_params(colors="white")
                self.ax2.grid(True, color="gray", linestyle="--", alpha=0.5)

                self.canvas.draw()
                self.last_graph_update = current_time

            self.status_bar.config(text=f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update data: {str(e)}")
            self.status_bar.config(text=f"Error: {str(e)}")

    def update_table(self):
        selected_pid = self.selected_pid
        for item in self.tree.get_children():
            self.tree.delete(item)

        start_idx = self.current_page * self.processes_per_page
        end_idx = start_idx + self.processes_per_page
        page_data = self.filtered_processes.iloc[start_idx:end_idx]

        for _, row in page_data.iterrows():
            state = row['state']
            tag = "running" if state == "running" else "stopped" if state == "stopped" else "other"
            self.tree.insert('', 'end', values=(row['pid'], row['name'], state, row['cpu_percent'], row['memory_mb'], row['duration']), tags=(tag,))
        self.tree.tag_configure("running", background="#388E3C", foreground="white")
        self.tree.tag_configure("stopped", background="#D32F2F", foreground="white")
        self.tree.tag_configure("other", background="#FFCA28", foreground="black")

        if selected_pid:
            for item in self.tree.get_children():
                if int(self.tree.item(item)['values'][0]) == selected_pid:
                    self.tree.selection_set(item)
                    self.selected_pid = selected_pid
                    break

        total_pages = (len(self.filtered_processes) + self.processes_per_page - 1) // self.processes_per_page
        self.page_var.set(f"Page {self.current_page + 1} of {total_pages}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        total_pages = (len(self.filtered_processes) + self.processes_per_page - 1) // self.processes_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_table()

    def debounce_search(self, *args):
        if self.search_after_id is not None:
            self.root.after_cancel(self.search_after_id)
        self.search_after_id = self.root.after(300, self.search_processes)

    def search_processes(self):
        try:
            self.current_page = 0
            search_term = self.search_var.get().strip().lower()
            if not search_term:
                self.filtered_processes = self.all_processes
            else:
                self.filtered_processes = self.all_processes[self.all_processes['name'].str.lower().str.contains(search_term, na=False)]
            self.update_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search processes: {str(e)}")

    def clear_search(self):
        self.search_var.set("")
        self.current_page = 0
        self.filtered_processes = self.all_processes
        self.update_table()

    def refresh_now(self):
        print("Refresh Now button clicked")
        try:
            self.update_data_once()
            messagebox.showinfo("Success", "Data refreshed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")

    def terminate_selected(self):
        print("Terminate Process button clicked")
        try:
            selected = self.tree.selection()
            print(f"Selected items: {selected}")
            if not selected:
                messagebox.showwarning("Warning", "Please select a process to terminate.")
                return
            pid = int(self.tree.item(selected[0])['values'][0])
            print(f"Terminating PID: {pid}")
            success, message = terminate_process(pid)
            if success:
                messagebox.showinfo("Success", message)
                self.selected_pid = None
                self.update_data_once()
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to terminate process: {str(e)}")

    def show_details(self):
        print("Show Details button clicked")
        try:
            selected = self.tree.selection()
            print(f"Selected items: {selected}")
            if not selected:
                messagebox.showwarning("Warning", "Please select a process to view details.")
                return
            pid = int(self.tree.item(selected[0])['values'][0])
            print(f"Showing details for PID: {pid}")
            details = get_process_details(pid)
            if "error" in details:
                messagebox.showerror("Error", details["error"])
                self.update_data_once()
            else:
                messagebox.showinfo("Process Details", f"Start Time: {datetime.fromtimestamp(details['start_time']).strftime('%Y-%m-%d %H:%M:%S')}\nUser: {details['user']}\nThreads: {details['threads']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch process details: {str(e)}")
            self.update_data_once()

    def deselect_process(self):
        print("Deselect button clicked")
        self.tree.selection_remove(self.tree.selection())
        self.selected_pid = None
        print("Selection cleared")

    def on_closing(self):
        self.running = False
        self.update_thread.join()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcessMonitorDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()