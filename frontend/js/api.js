const API_URL = "http://127.0.0.1:8080";

export async function fetchTasks() {
  const response = await fetch(`${API_URL}/tasks`);
  const data = await response.json();
  return data.items;
}