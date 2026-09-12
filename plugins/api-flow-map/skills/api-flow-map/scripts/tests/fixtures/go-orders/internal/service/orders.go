package service

import (
	"context"
	"errors"
	"fmt"
	"log/slog"

	"github.com/acme/orders/internal/clients"
	"github.com/acme/orders/internal/store"
)

var ErrNotFound = errors.New("order not found")
var ErrOutOfStock = errors.New("out of stock")

const reviewThreshold = 1000

type OrderService struct {
	store     *store.OrderStore
	payments  *clients.PaymentsClient
	inventory *clients.InventoryClient
	events    *clients.EventPublisher
	flags     clients.FeatureFlags
}

func New() *OrderService { return &OrderService{} }

func (s *OrderService) GetOrder(ctx context.Context, id string) (*store.Order, error) {
	order, err := s.store.FindByID(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("lookup order: %w", err)
	}
	if order == nil {
		return nil, ErrNotFound
	}
	return order, nil
}

func (s *OrderService) PlaceOrder(ctx context.Context, req CreateOrderRequest) (*store.Order, error) {
	if len(req.Items) == 0 {
		return nil, errors.New("order must contain items")
	}
	order := store.NewOrder(req.Items)
	reserved, err := s.inventory.Reserve(ctx, order.Items)
	if err != nil {
		return nil, err
	}
	if !reserved.OK {
		return nil, ErrOutOfStock
	}
	if order.Total > reviewThreshold && s.flags.Enabled("manual-review") {
		order.Status = "UNDER_REVIEW"
		if err := s.store.Save(ctx, order); err != nil {
			return nil, err
		}
		s.events.Publish(ctx, "order-events", "ORDER_FLAGGED", order.ID)
		return order, nil
	}
	charge, err := s.payments.Charge(ctx, order.Total, req.PaymentToken)
	if err != nil {
		s.inventory.Release(ctx, order.Items)
		return nil, fmt.Errorf("charge: %w", err)
	}
	order.PaymentID = charge.ID
	order.Status = "CONFIRMED"
	if err := s.store.Save(ctx, order); err != nil {
		return nil, err
	}
	slog.Info("order placed", "id", order.ID)
	s.events.Publish(ctx, "order-events", "ORDER_PLACED", order.ID)
	return order, nil
}

func (s *OrderService) Cancel(ctx context.Context, id string) error {
	order, err := s.GetOrder(ctx, id)
	if err != nil {
		return err
	}
	switch order.Status {
	case "CONFIRMED":
		if err := s.payments.Refund(ctx, order.PaymentID); err != nil {
			return err
		}
		s.inventory.Release(ctx, order.Items)
	case "UNDER_REVIEW":
	default:
		return fmt.Errorf("cannot cancel order in status %s", order.Status)
	}
	order.Status = "CANCELLED"
	if err := s.store.Save(ctx, order); err != nil {
		return err
	}
	s.events.Publish(ctx, "order-events", "ORDER_CANCELLED", order.ID)
	return nil
}

type CreateOrderRequest struct {
	Items        []store.Item
	PaymentToken string
}
