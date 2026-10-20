<?php
/**
 * La Cuisine de Jeanine — réception du formulaire de devis.
 * Hébergement Hostinger : la fonction mail() envoie depuis le domaine.
 * Pour changer l'adresse de réception, modifier $DEST ci-dessous.
 */
declare(strict_types=1);
date_default_timezone_set('Europe/Paris');

$DEST = 'contact@lacuisinedejeanine.fr';
$FROM = 'contact@lacuisinedejeanine.fr';   // doit être une adresse du domaine

$wantsJson = stripos($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json') !== false;

function reply(bool $ok, string $error = ''): void {
    global $wantsJson;
    if ($wantsJson) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(['ok' => $ok, 'error' => $error], JSON_UNESCAPED_UNICODE);
    } else {
        header('Location: /?envoi=' . ($ok ? 'ok' : 'erreur') . '#devis', true, 303);
    }
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    reply(false, 'Méthode non autorisée.');
}

function field(string $k, int $max = 200): string {
    $v = trim((string)($_POST[$k] ?? ''));
    $v = str_replace(["\r", "\0"], '', $v);
    return mb_substr($v, 0, $max);
}

// --- anti-spam ---
if (field('site_web') !== '') reply(true);                      // robot : on fait semblant
$ts = (int)field('ts', 20);
if ($ts > 0 && (microtime(true) * 1000 - $ts) < 3000) reply(true); // envoyé en moins de 3 s

$ip = $_SERVER['REMOTE_ADDR'] ?? 'x';
$rl = sys_get_temp_dir() . '/lcdj_rl_' . hash('sha256', $ip . __DIR__ . date('Y-m-d'));
$hits = array_filter(explode(',', @file_get_contents($rl) ?: ''), fn($t) => $t && $t > time() - 3600);
if (count($hits) >= 5) reply(false, 'Trop de demandes envoyées. Réessayez plus tard ou écrivez-nous à contact@lacuisinedejeanine.fr.');
$hits[] = time();
@file_put_contents($rl, implode(',', $hits));

// --- validation ---
$nom        = str_replace("\n", ' ', field('nom', 120));
$entreprise = str_replace("\n", ' ', field('entreprise', 120));
$email      = str_replace("\n", '', field('email', 160));
$tel        = str_replace("\n", ' ', field('telephone', 30));
$message    = field('message', 3000);
$interets   = array_map(fn($x) => mb_substr(str_replace(["\r","\n"], '', (string)$x), 0, 60),
                        array_slice((array)($_POST['interet'] ?? []), 0, 6));

if ($nom === '' || $entreprise === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    reply(false, 'Merci de renseigner votre nom, votre entreprise et une adresse email valide.');
}

// --- email ---
$sujet = 'Demande de devis — ' . $entreprise . ($interets ? ' (' . implode(', ', $interets) . ')' : '');
$corps = "Nouvelle demande depuis le site lacuisinedejeanine.fr\n\n"
       . "Nom : $nom\n"
       . "Entreprise : $entreprise\n"
       . "Email : $email\n"
       . "Téléphone : " . ($tel ?: '—') . "\n"
       . "Intéressé par : " . ($interets ? implode(', ', $interets) : '—') . "\n\n"
       . "Message :\n" . ($message ?: '—') . "\n\n"
       . "---\nEnvoyé le " . date('d/m/Y à H:i') . "\n";

$headers = [
    'From' => 'Site La Cuisine de Jeanine <' . $FROM . '>',
    'Reply-To' => $email,
    'Content-Type' => 'text/plain; charset=UTF-8',
    'X-Mailer' => 'PHP',
];
$ok = mail($DEST, '=?UTF-8?B?' . base64_encode($sujet) . '?=', $corps, $headers, '-f' . $FROM);

reply($ok, $ok ? '' : "L'envoi a échoué. Écrivez-nous à contact@lacuisinedejeanine.fr.");
