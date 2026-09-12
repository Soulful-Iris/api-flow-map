package main

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/acme/orders/internal/handlers"
	"github.com/acme/orders/internal/service"
)

func main() {
	r := chi.NewRouter()
	h := handlers.NewOrderHandler(service.New())
	r.Get("/healthz", handlers.Healthz)
	r.Route("/api/v1", func(r chi.Router) {
		r.Use(handlers.Authenticate)
		r.Route("/orders", func(r chi.Router) {
			r.Get("/{id}", h.GetOrder)
			r.With(handlers.RequireScope("orders:write")).Post("/", h.CreateOrder)
			r.Post("/{id}/cancel", h.CancelOrder)
		})
	})
	http.ListenAndServe(":8080", r)
}
