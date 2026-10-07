import { useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { novedadesExpedientes } from '../api/agenda';
import { origen } from '../shared/helpers/expedientes';

export default function ReservasNotifications() {
  const cursor = useRef(null);
  const processed = useRef(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const updates = useQuery({
    queryKey: ['reservas-externas'],
    queryFn: async ({ signal }) => {
      const data = await novedadesExpedientes(cursor.current, signal);
      cursor.current = data.cursor;
      return data;
    },
    refetchInterval: 3000,
    gcTime: 0,
  });

  useEffect(() => {
    if (!updates.data?.results.length || processed.current === updates.data) return;
    processed.current = updates.data;
    queryClient.invalidateQueries({ queryKey: ['expedientes'] });
    for (const registro of updates.data.results) {
      toast.success(`Expediente N.º ${registro.numero_formateado} reservado.`, {
        id: `reserva-${registro.id}`,
        description: `${origen(registro.origen)} · ${registro.causante}`,
        action: { label: 'Ver expediente', onClick: () => navigate(`/expedientes/${registro.id}`) },
      });
    }
  }, [updates.data, queryClient, navigate]);

  return null;
}
