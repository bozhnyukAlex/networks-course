import matplotlib.pyplot as plt

F = 15 * 1000
u_s = 30
d_i = 2
N_values = [10, 100, 1000]
u_values = [0.3, 0.7, 2]


def client_server_time(F, N, u_s, d_i):
    server_time = (F * N) / u_s
    peer_time = F / d_i
    return max(server_time, peer_time)


def p2p_time(F, N, u_s, d_i, u):
    server_time = F / u_s
    peer_time = F / d_i
    total_upload_time = (F * N) / (u_s + N * u)
    return max(server_time, peer_time, total_upload_time)


cs_times = [client_server_time(F, N, u_s, d_i) for N in N_values]
p2p_times = {u: [p2p_time(F, N, u_s, d_i, u) for N in N_values] for u in u_values}

plt.figure(figsize=(10, 6))

plt.plot(N_values, cs_times, marker='o', linestyle='-', color='black', label='Клиент-сервер')

colors = ['blue', 'green', 'red']
for i, u in enumerate(u_values):
    plt.plot(N_values, p2p_times[u], marker='o', linestyle='--', color=colors[i],
             label=f'P2P, u = {u} Мбит/с')

plt.xscale('log')
plt.yscale('log')
plt.xlabel('Число пиров (N)')
plt.ylabel('Минимальное время раздачи (с)')
plt.title('Минимальное время раздачи файла (F = 15 Гбит)')
plt.grid(True, which="both", ls="--")
plt.legend()

plt.show()
