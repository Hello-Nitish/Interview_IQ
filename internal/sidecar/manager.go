package sidecar

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"
)

// Manager handles the lifecycle of the Python DirectML sidecar subprocess.
type Manager struct {
	pythonPath string
	port       int
	token      string
	cmd        *exec.Cmd
	client     *Client
	mu         sync.Mutex
	isRunning  bool
}

// NewManager initializes a sidecar process manager.
func NewManager(pythonPath string, port int) *Manager {
	if pythonPath == "" {
		// Auto-detect project virtualenv on Windows
		cwd, err := os.Getwd()
		if err == nil {
			venvPython := filepath.Join(cwd, ".venv", "Scripts", "python.exe")
			if _, err := os.Stat(venvPython); err == nil {
				pythonPath = venvPython
			}
		}
		if pythonPath == "" {
			pythonPath = "python"
		}
	}

	return &Manager{
		pythonPath: pythonPath,
		port:       port,
	}
}

// generateSecureToken creates a 32-byte cryptographically secure hex string.
func generateSecureToken() string {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		return fmt.Sprintf("interviewiq-%d", time.Now().UnixNano())
	}
	return hex.EncodeToString(bytes)
}

// findFreePort locates an available TCP port on localhost.
func findFreePort() (int, error) {
	addr, err := net.ResolveTCPAddr("tcp", "127.0.0.1:0")
	if err != nil {
		return 0, err
	}
	l, err := net.ListenTCP("tcp", addr)
	if err != nil {
		return 0, err
	}
	defer l.Close()
	return l.Addr().(*net.TCPAddr).Port, nil
}

// Start spawns the Python sidecar and waits for /health readiness.
func (m *Manager) Start() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.isRunning {
		return nil
	}

	if m.port <= 0 {
		freePort, err := findFreePort()
		if err != nil {
			m.port = 8000
		} else {
			m.port = freePort
		}
	}

	m.token = generateSecureToken()
	baseURL := fmt.Sprintf("http://127.0.0.1:%d", m.port)

	log.Printf("[SidecarManager] Spawning Python DirectML Sidecar on %s with Python: %s", baseURL, m.pythonPath)

	cmd := exec.Command(m.pythonPath, "-m", "sidecar.server",
		"--host", "127.0.0.1",
		"--port", fmt.Sprintf("%d", m.port),
		"--token", m.token,
	)

	// Pipe output for logging
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start Python sidecar: %w", err)
	}

	m.cmd = cmd
	m.isRunning = true
	m.client = NewClient(baseURL, m.token)

	// Wait for health endpoint readiness (up to 15 seconds)
	ready := false
	healthURL := fmt.Sprintf("%s/health", baseURL)
	for i := 0; i < 30; i++ {
		time.Sleep(500 * time.Millisecond)
		resp, err := http.Get(healthURL)
		if err == nil && resp.StatusCode == http.StatusOK {
			body, _ := io.ReadAll(resp.Body)
			resp.Body.Close()
			log.Printf("[SidecarManager] Sidecar is healthy and ready: %s", string(body))
			ready = true
			break
		}
	}

	if !ready {
		_ = m.Stop()
		return fmt.Errorf("sidecar failed to respond on %s within 15 seconds", healthURL)
	}

	return nil
}

// Stop gracefully terminates the Python sidecar.
func (m *Manager) Stop() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.isRunning || m.cmd == nil || m.cmd.Process == nil {
		return nil
	}

	log.Println("[SidecarManager] Stopping Python DirectML sidecar process...")
	err := m.cmd.Process.Kill()
	m.isRunning = false
	return err
}

// GetClient returns the authenticated HTTP client for calling sidecar APIs.
func (m *Manager) GetClient() *Client {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.client
}

// GetPort returns the active port.
func (m *Manager) GetPort() int {
	return m.port
}
